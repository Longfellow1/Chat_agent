from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

# Load .env.agent file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env.agent"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, try manual load
    env_path = Path(__file__).parent.parent / ".env.agent"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

from app.api.server import run_server
from app.factory import build_flow
from app.schemas.contracts import ChatRequest


def run_chat(query: str) -> None:
    flow = build_flow()
    resp = flow.run(ChatRequest(query=query))
    print(json.dumps(resp.to_dict(), ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent service runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_chat = sub.add_parser("chat", help="run single-turn chat in CLI mode")
    p_chat.add_argument("query", help="single-turn user query")

    sub.add_parser("serve", help="run HTTP server")

    args = parser.parse_args()
    if args.cmd == "serve":
        run_server()
        return

    if args.cmd == "chat":
        run_chat(args.query)
        return


if __name__ == "__main__":
    main()
