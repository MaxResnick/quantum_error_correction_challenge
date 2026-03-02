#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cleanup_stale_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$pid_file"
    fi
  fi
}

if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
  echo "Missing virtualenv at $ROOT_DIR/.venv"
  echo "Create it with: python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[server,dev]'"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found in PATH"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "docker daemon is not running"
  exit 1
fi

if ! docker image inspect qec-benchmark-evaluator:latest >/dev/null 2>&1; then
  echo "Building evaluator image..."
  docker build -t qec-benchmark-evaluator:latest -f docker/evaluator.Dockerfile .
fi

mkdir -p .mvp/logs .mvp/run .qec_submissions

cleanup_stale_pid .mvp/run/api.pid
cleanup_stale_pid .mvp/run/worker.pid

export QEC_DATASET_DIR="${QEC_DATASET_DIR:-$ROOT_DIR/data/mvp10_hard}"
export QEC_DB_URL="${QEC_DB_URL:-sqlite:///$ROOT_DIR/.mvp/qec_benchmark_mvp.db}"
export QEC_SUBMISSIONS_DIR="${QEC_SUBMISSIONS_DIR:-$ROOT_DIR/.qec_submissions}"
export QEC_DOCKER_IMAGE="${QEC_DOCKER_IMAGE:-qec-benchmark-evaluator:latest}"

if lsof -iTCP:8000 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  if [[ ! -f .mvp/run/api.pid ]]; then
    echo "Port 8000 is already in use by another process"
    lsof -iTCP:8000 -sTCP:LISTEN -n -P || true
    exit 1
  fi
fi

if [[ ! -d "$QEC_DATASET_DIR/private_test" ]]; then
  echo "Dataset not found at $QEC_DATASET_DIR"
  echo "Generate one with: qec-benchmark-generate --output data/mvp10_hard --shots 200000 --grid mvp10 --seed 7 --overwrite"
  exit 1
fi

if [[ -f .mvp/run/api.pid ]] && kill -0 "$(cat .mvp/run/api.pid)" 2>/dev/null; then
  echo "API already running (pid $(cat .mvp/run/api.pid))"
else
  nohup "$ROOT_DIR/.venv/bin/qec-benchmark-server" > .mvp/logs/api.log 2>&1 &
  echo $! > .mvp/run/api.pid
  echo "Started API pid $(cat .mvp/run/api.pid)"
fi

if [[ -f .mvp/run/worker.pid ]] && kill -0 "$(cat .mvp/run/worker.pid)" 2>/dev/null; then
  echo "Worker already running (pid $(cat .mvp/run/worker.pid))"
else
  nohup "$ROOT_DIR/.venv/bin/qec-benchmark-worker" > .mvp/logs/worker.log 2>&1 &
  echo $! > .mvp/run/worker.pid
  echo "Started worker pid $(cat .mvp/run/worker.pid)"
fi

for _ in $(seq 1 40); do
  if curl -sS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if ! curl -sS http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "API did not become healthy on http://127.0.0.1:8000/health"
  if [[ -f .mvp/logs/api.log ]]; then
    echo "--- api.log tail ---"
    tail -n 30 .mvp/logs/api.log || true
  fi
  exit 1
fi

if [[ -f .mvp/run/worker.pid ]] && ! kill -0 "$(cat .mvp/run/worker.pid)" 2>/dev/null; then
  echo "Worker failed to stay running"
  if [[ -f .mvp/logs/worker.log ]]; then
    echo "--- worker.log tail ---"
    tail -n 30 .mvp/logs/worker.log || true
  fi
  exit 1
fi

echo "MVP stack started"
echo "  API:    http://127.0.0.1:8000"
echo "  Health: http://127.0.0.1:8000/health"
echo "  Logs:   $ROOT_DIR/.mvp/logs"
