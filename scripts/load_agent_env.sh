#!/usr/bin/env bash
set -euo pipefail

# Load persistent local env for agent runtime.
# Priority (low -> high): .env, .env.agent, .env.local
ROOT_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"

load_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$f"
    set +a
  fi
}

load_file "$ROOT_DIR/.env"
load_file "$ROOT_DIR/.env.agent"
load_file "$ROOT_DIR/.env.local"

