#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Case:
    query: str
    expect_tool: str


SMOKE_CASES: list[Case] = [
    Case("上证指数今天走势", "get_stock"),
    Case("600519股价", "get_stock"),
    Case("郑州今天天气怎么样", "get_weather"),
    Case("郑州今天穿衣指数怎样", "get_weather"),
    Case("郑州东站附近餐厅", "find_nearby"),
    Case("查一下今天AI新闻", "get_news"),
    Case("OpenAI官网", "web_search"),
    Case("帮我规划去杭州两日游", "plan_trip"),
]


def call_chat(base_url: str, query: str, timeout: float) -> dict:
    url = base_url.rstrip("/") + "/chat"
    payload = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    passed = 0
    start = time.time()
    rows: list[dict] = []
    for i, c in enumerate(SMOKE_CASES, 1):
        try:
            out = call_chat(args.base_url, c.query, args.timeout)
            data = out.get("data", {})
            tool = data.get("tool_name")
            status = data.get("tool_status")
            ok = tool == c.expect_tool and status in {"ok", "missing_slots"}
            passed += int(ok)
            rows.append(
                {
                    "idx": i,
                    "query": c.query,
                    "expect_tool": c.expect_tool,
                    "got_tool": tool,
                    "tool_status": status,
                    "tool_provider": data.get("tool_provider"),
                    "fallback_chain": data.get("fallback_chain"),
                    "total_ms": data.get("latency_ms", {}).get("total"),
                    "passed": ok,
                }
            )
            print(
                f"[{i:02d}] {'PASS' if ok else 'FAIL'} "
                f"query={c.query} expect={c.expect_tool} got={tool} "
                f"status={status} provider={data.get('tool_provider')} "
                f"fallback={data.get('fallback_chain')} total_ms={data.get('latency_ms', {}).get('total')}"
            )
        except Exception as e:  # noqa: BLE001
            rows.append(
                {
                    "idx": i,
                    "query": c.query,
                    "expect_tool": c.expect_tool,
                    "got_tool": None,
                    "tool_status": "exception",
                    "tool_provider": None,
                    "total_ms": None,
                    "passed": False,
                    "error": str(e),
                }
            )
            print(f"[{i:02d}] FAIL query={c.query} err={e}")

    cost = int((time.time() - start) * 1000)
    print(f"\nsmoke_result: {passed}/{len(SMOKE_CASES)} passed, cost_ms={cost}")
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "base_url": args.base_url,
                    "passed": passed,
                    "total": len(SMOKE_CASES),
                    "cost_ms": cost,
                    "rows": rows,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"smoke_report: {p}")
    return 0 if passed == len(SMOKE_CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
