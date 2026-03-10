#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Load persisted project env if present.
# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_agent_env.sh" "$ROOT_DIR"

export PYTHONPATH="$ROOT_DIR/agent_service:${PYTHONPATH:-}"
python3 agent_service/main.py chat "$@"
