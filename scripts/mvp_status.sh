#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

check_pid() {
  local pid_file="$1"
  local name="$2"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "$name: running (pid $pid)"
    else
      echo "$name: stale pid file (pid $pid)"
    fi
  else
    echo "$name: not started"
  fi
}

check_pid .mvp/run/api.pid "api"
check_pid .mvp/run/worker.pid "worker"

if command -v curl >/dev/null 2>&1; then
  code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/health || true)"
  echo "health_http: ${code:-unreachable}"
fi

if [[ -f .mvp/logs/api.log ]]; then
  echo "--- api.log tail ---"
  tail -n 15 .mvp/logs/api.log || true
fi

if [[ -f .mvp/logs/worker.log ]]; then
  echo "--- worker.log tail ---"
  tail -n 15 .mvp/logs/worker.log || true
fi
