#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="$ROOT_DIR/agent_service:${PYTHONPATH:-}"
python3 scripts/run_smoke_tools.py "$@"

