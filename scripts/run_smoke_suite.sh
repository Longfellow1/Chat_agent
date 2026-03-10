#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

BASE_URL="${1:-http://127.0.0.1:8011}"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="eval/reports/smoke_${TS}"
mkdir -p "$OUT_DIR"

echo "running smoke -> $OUT_DIR"
./scripts/run_smoke_tools.sh --base-url "$BASE_URL" --out "$OUT_DIR/smoke_tools.json"

echo "done: $OUT_DIR"
