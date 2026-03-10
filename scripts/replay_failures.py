#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path


def call_chat(base_url: str, query: str, timeout: float) -> dict:
    url = base_url.rstrip("/") + "/chat"
    payload = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--input", required=True, help="smoke report json path")
    parser.add_argument("--out", default="", help="replay output json path")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--max", type=int, default=20)
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"input not found: {src}")

    data = json.loads(src.read_text(encoding="utf-8"))
    rows = data.get("rows") or []
    failed = [r for r in rows if not r.get("passed")]
    failed = failed[: max(1, args.max)]

    print(f"replay_source: {src}")
    print(f"failed_cases: {len(failed)}")
    if not failed:
        print("nothing to replay")
        return 0

    out_rows: list[dict] = []
    start = time.time()
    recovered = 0
    for i, r in enumerate(failed, 1):
        q = str(r.get("query") or "")
        expect_tool = r.get("expect_tool")
        try:
            resp = call_chat(args.base_url, q, args.timeout)
            payload = resp.get("data", {})
            got_tool = payload.get("tool_name")
            status = payload.get("tool_status")
            ok = got_tool == expect_tool and status in {"ok", "missing_slots"}
            recovered += int(ok)
            out_rows.append(
                {
                    "idx": i,
                    "query": q,
                    "expect_tool": expect_tool,
                    "got_tool": got_tool,
                    "tool_status": status,
                    "tool_provider": payload.get("tool_provider"),
                    "fallback_chain": payload.get("fallback_chain"),
                    "total_ms": payload.get("latency_ms", {}).get("total"),
                    "recovered": ok,
                }
            )
            print(
                f"[{i:02d}] {'RECOVERED' if ok else 'FAILED'} "
                f"query={q} expect={expect_tool} got={got_tool} status={status}"
            )
        except Exception as e:  # noqa: BLE001
            out_rows.append(
                {
                    "idx": i,
                    "query": q,
                    "expect_tool": expect_tool,
                    "recovered": False,
                    "error": str(e),
                }
            )
            print(f"[{i:02d}] FAILED query={q} err={e}")

    cost_ms = int((time.time() - start) * 1000)
    print(f"\nreplay_result: {recovered}/{len(failed)} recovered, cost_ms={cost_ms}")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {
                    "source": str(src),
                    "base_url": args.base_url,
                    "failed_total": len(failed),
                    "recovered": recovered,
                    "cost_ms": cost_ms,
                    "rows": out_rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"replay_report: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

