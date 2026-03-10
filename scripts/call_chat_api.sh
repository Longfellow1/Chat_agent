#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
QUERY="${2:-今天天气怎么样}"
SESSION_ID="${3:-}"

if [[ -n "${SESSION_ID}" ]]; then
  BODY="{\"query\":\"${QUERY}\",\"session_id\":\"${SESSION_ID}\"}"
else
  BODY="{\"query\":\"${QUERY}\"}"
fi

curl -sS -X POST "${BASE_URL}/chat" \
  -H 'Content-Type: application/json' \
  -d "${BODY}"
echo
