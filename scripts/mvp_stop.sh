#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

stop_pid_file() {
  local pid_file="$1"
  local name="$2"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 0.2
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
      echo "Stopped $name (pid $pid)"
    else
      echo "$name not running"
    fi
    rm -f "$pid_file"
  else
    echo "$name pid file not found"
  fi
}

stop_pid_file .mvp/run/worker.pid "worker"
stop_pid_file .mvp/run/api.pid "api"

# Fallback cleanup: if a qec-benchmark server is still holding port 8000, stop it.
if command -v lsof >/dev/null 2>&1; then
  api_pid="$(lsof -tiTCP:8000 -sTCP:LISTEN -n -P 2>/dev/null || true)"
  if [[ -n "$api_pid" ]]; then
    cmd="$(ps -p "$api_pid" -o command= 2>/dev/null || true)"
    if [[ "$cmd" == *"qec-benchmark-server"* ]]; then
      kill "$api_pid" 2>/dev/null || true
      sleep 0.2
      if kill -0 "$api_pid" 2>/dev/null; then
        kill -9 "$api_pid" 2>/dev/null || true
      fi
      echo "Stopped api fallback (pid $api_pid)"
    fi
  fi
fi
