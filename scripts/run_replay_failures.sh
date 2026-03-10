#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

INPUT="${1:-}"
BASE_URL="${2:-http://127.0.0.1:8011}"
if [[ -z "$INPUT" ]]; then
  echo "usage: $0 <smoke_report_json> [base_url]"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
OUT="eval/reports/replay_${TS}.json"

export PYTHONPATH="$ROOT_DIR/agent_service:${PYTHONPATH:-}"
python3 scripts/replay_failures.py --input "$INPUT" --base-url "$BASE_URL" --out "$OUT"
echo "done: $OUT"

