from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


def gen_trace_id() -> str:
    return uuid.uuid4().hex


def trace_file_path() -> Path:
    root = Path(os.getenv("TRACE_DIR", "traces"))
    root.mkdir(parents=True, exist_ok=True)
    day = time.strftime("%Y%m%d")
    return root / f"agent_service_{day}.jsonl"


def write_trace(event: dict[str, Any]) -> None:
    path = trace_file_path()
    record = dict(event)
    record.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
