#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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


def load_queries(csv_path: Path, limit: int) -> list[str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        key = None
        for cand in ("query", "Query", "text", "input", "question"):
            if cand in cols:
                key = cand
                break
        if key is None:
            raise RuntimeError(f"CSV缺少query列，可用列: {cols}")
        out: list[str] = []
        for r in reader:
            q = (r.get(key) or "").strip()
            if q:
                out.append(q)
            if len(out) >= limit:
                break
        return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--csv", default="testset_eval_1000_v3_sample5p.csv")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir) if args.out_dir else Path("eval/reports") / f"chatapi_eval_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    queries = load_queries(Path(args.csv), args.limit)
    rows: list[dict] = []
    latencies: list[int] = []
    start = time.time()
    for i, q in enumerate(queries, 1):
        try:
            resp = call_chat(args.base_url, q, args.timeout)
            d = resp.get("data", {})
            total_ms = int(d.get("latency_ms", {}).get("total") or 0)
            latencies.append(total_ms)
            rows.append(
                {
                    "idx": i,
                    "query": q,
                    "answer": d.get("final_text", ""),
                    "latency_ms": total_ms,
                }
            )
            print(f"[{i:02d}] {total_ms}ms | {q}")
        except Exception as e:  # noqa: BLE001
            rows.append({"idx": i, "query": q, "answer": "", "latency_ms": None, "error": str(e)})
            print(f"[{i:02d}] ERROR | {q} | {e}")

    # write csv
    out_csv = out_dir / "answers_latency.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["idx", "query", "answer", "latency_ms", "error"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # summary
    ok_lat = [x for x in latencies if x > 0]
    ok_lat.sort()
    avg = round(sum(ok_lat) / len(ok_lat), 2) if ok_lat else None
    p95 = ok_lat[int(0.95 * (len(ok_lat) - 1))] if ok_lat else None
    summary = {
        "total": len(rows),
        "ok": len(ok_lat),
        "avg_latency_ms": avg,
        "p95_latency_ms": p95,
        "cost_ms": int((time.time() - start) * 1000),
    }
    out_json = out_dir / "summary.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsummary: {summary}")
    print(f"report: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

