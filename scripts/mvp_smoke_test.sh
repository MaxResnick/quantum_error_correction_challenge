#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_URL="${QEC_API_URL:-http://127.0.0.1:8000}"
SUBMISSION_NAME="${QEC_SMOKE_SUBMISSION_NAME:-smoke-test-$(date +%s)}"
MAX_POLLS="${QEC_SMOKE_MAX_POLLS:-90}"
POLL_SECONDS="${QEC_SMOKE_POLL_SECONDS:-2}"

if [[ ! -f "examples/submission_template.py" ]]; then
  echo "missing examples/submission_template.py"
  exit 1
fi

./scripts/mvp_start.sh

health_code="000"
for _ in $(seq 1 40); do
  health_code="$(curl -s -o /dev/null -w '%{http_code}' "$API_URL/health" || true)"
  if [[ "$health_code" == "200" ]]; then
    break
  fi
  sleep 0.25
done
if [[ "$health_code" != "200" ]]; then
  echo "health check failed at $API_URL/health (status $health_code)"
  exit 1
fi

echo "Submitting example decoder as '$SUBMISSION_NAME'..."
submit_json="$(curl -sS -X POST "$API_URL/submissions/python?name=$SUBMISSION_NAME" -F file=@examples/submission_template.py)"
if [[ -z "$submit_json" ]]; then
  echo "empty submission response from API"
  exit 1
fi
submission_id="$(
  printf '%s' "$submit_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'
)"
echo "Submission queued with id=$submission_id"

final_json=""
final_status=""
for ((i=1; i<=MAX_POLLS; i++)); do
  current_json="$(curl -sS "$API_URL/submissions/$submission_id")"
  current_status="$(
    printf '%s' "$current_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])'
  )"
  echo "poll $i/$MAX_POLLS: status=$current_status"
  if [[ "$current_status" == "succeeded" || "$current_status" == "failed" ]]; then
    final_json="$current_json"
    final_status="$current_status"
    break
  fi
  sleep "$POLL_SECONDS"
done

if [[ -z "$final_status" ]]; then
  echo "timed out waiting for submission completion"
  exit 1
fi

echo "Final submission record:"
printf '%s\n' "$final_json" | python3 -m json.tool

if [[ "$final_status" != "succeeded" ]]; then
  echo "smoke test failed: submission ended with status=$final_status"
  exit 1
fi

echo "Leaderboard snapshot:"
curl -sS "$API_URL/leaderboard" | python3 -m json.tool
echo "MVP smoke test passed"
