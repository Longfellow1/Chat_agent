#!/usr/bin/env python3
"""
完整端到端评测脚本

支持:
- 从CSV加载评测数据
- 工具名称映射
- 准确率计算
- 详细报告生成

Usage:
    python scripts/run_full_eval.py --csv archive/csv_data/testset_eval_1000_v3.csv --limit 800
"""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


# 工具名称映射（数据集 → 实现）
TOOL_NAME_MAPPING = {
    "search_nearby": "find_nearby",
}


@dataclass
class TestCase:
    """评测用例"""
    sample_id: str
    query: str
    sample_type: str
    scenario: str
    category: str
    expected_tool: Optional[str]
    expected_behavior: Optional[str]
    risk_tag: str


@dataclass
class TestResult:
    """评测结果"""
    sample_id: str
    query: str
    expected_tool: Optional[str]
    expected_behavior: Optional[str]
    got_tool: Optional[str]
    got_mode: Optional[str]
    tool_status: Optional[str]
    tool_provider: Optional[str]
    fallback_chain: list
    latency_ms: Optional[int]
    passed: bool
    error: Optional[str] = None
    trace: Optional[dict] = None  # Full response data for analysis


def call_chat(base_url: str, query: str, timeout: float) -> dict:
    """调用chat接口"""
    url = base_url.rstrip("/") + "/chat"
    payload = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        url, 
        data=payload, 
        headers={"Content-Type": "application/json"}, 
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_test_cases(csv_path: Path, limit: int) -> list[TestCase]:
    """从CSV加载评测用例"""
    cases = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Support both "query" and "question" fields
            query_text = row.get("query", "") or row.get("question", "")
            case = TestCase(
                sample_id=row.get("sample_id", ""),
                query=query_text.strip(),
                sample_type=row.get("sample_type", ""),
                scenario=row.get("scenario", ""),
                category=row.get("category", ""),
                expected_tool=row.get("expected_tool", "").strip() or None,
                expected_behavior=row.get("expected_behavior", "").strip() or None,
                risk_tag=row.get("risk_tag", ""),
            )
            if case.query:
                cases.append(case)
            if len(cases) >= limit:
                break
    return cases


def validate_result(case: TestCase, response: dict) -> bool:
    """验证结果是否符合预期"""
    data = response.get("data", {})
    got_tool = data.get("tool_name")
    got_mode = data.get("decision_mode")
    tool_status = data.get("tool_status")
    tool_provider = data.get("tool_provider", "")
    
    # CRITICAL: Reject any mock data
    if tool_provider and "mock" in tool_provider.lower():
        return False
    
    # 1. 工具调用类别验证
    if case.category == "工具调用":
        # 必须是tool_call模式
        if got_mode != "tool_call":
            return False
        
        # 工具名称验证（支持映射）
        if case.expected_tool:
            expected_tool = TOOL_NAME_MAPPING.get(case.expected_tool, case.expected_tool)
            if got_tool != expected_tool:
                return False
        
        # 工具状态验证（ok或missing_slots都算通过）
        if tool_status not in {"ok", "missing_slots"}:
            return False
        
        return True
    
    # 2. 拒识类别验证
    elif case.category == "拒识":
        # 必须是reject模式
        return got_mode == "reject"
    
    # 3. 闲聊类别验证
    elif case.category == "闲聊":
        # 可以是reply或end_chat模式
        if case.expected_behavior == "terminate_chat":
            return got_mode == "end_chat"
        else:
            return got_mode in {"reply", "end_chat"}
    
    # 4. 未知类别，默认通过
    return True


def run_evaluation(
    base_url: str,
    csv_path: Path,
    limit: int,
    timeout: float,
    out_dir: Path
) -> dict:
    """运行评测"""
    
    # 加载测试用例
    print(f"Loading test cases from {csv_path}...")
    cases = load_test_cases(csv_path, limit)
    print(f"Loaded {len(cases)} test cases\n")
    
    # 执行评测
    results: list[TestResult] = []
    start_time = time.time()
    
    for i, case in enumerate(cases, 1):
        try:
            # 调用API
            response = call_chat(base_url, case.query, timeout)
            data = response.get("data", {})
            
            # 验证结果
            passed = validate_result(case, response)
            
            # 记录结果（包含完整trace）
            result = TestResult(
                sample_id=case.sample_id,
                query=case.query,
                expected_tool=case.expected_tool,
                expected_behavior=case.expected_behavior,
                got_tool=data.get("tool_name"),
                got_mode=data.get("decision_mode"),
                tool_status=data.get("tool_status"),
                tool_provider=data.get("tool_provider"),
                fallback_chain=data.get("fallback_chain", []),
                latency_ms=data.get("latency_ms", {}).get("total"),
                passed=passed,
                trace=data,  # Store full response data
            )
            results.append(result)
            
            # 打印进度
            status = "✅ PASS" if passed else "❌ FAIL"
            print(
                f"[{i:03d}/{len(cases)}] {status} | "
                f"cat={case.category} | "
                f"exp={case.expected_tool or 'N/A'} | "
                f"got={result.got_tool or result.got_mode} | "
                f"{result.latency_ms}ms | "
                f"{case.query[:40]}"
            )
            
        except Exception as e:
            # 记录错误
            result = TestResult(
                sample_id=case.sample_id,
                query=case.query,
                expected_tool=case.expected_tool,
                expected_behavior=case.expected_behavior,
                got_tool=None,
                got_mode=None,
                tool_status="exception",
                tool_provider=None,
                fallback_chain=[],
                latency_ms=None,
                passed=False,
                error=str(e),
                trace=None,
            )
            results.append(result)
            
            print(
                f"[{i:03d}/{len(cases)}] ❌ ERROR | "
                f"{case.query[:40]} | {e}"
            )
    
    total_time = time.time() - start_time
    
    # 生成统计
    stats = generate_statistics(cases, results, total_time)
    
    # 保存报告
    save_reports(out_dir, results, stats)
    
    return stats


def generate_statistics(
    cases: list[TestCase],
    results: list[TestResult],
    total_time: float
) -> dict:
    """生成统计信息"""
    
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    # 分类别统计
    category_stats = {}
    for case, result in zip(cases, results):
        cat = case.category
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0}
        category_stats[cat]["total"] += 1
        category_stats[cat]["passed"] += int(result.passed)
    
    # 添加准确率
    for cat, stat in category_stats.items():
        stat["accuracy"] = round(stat["passed"] / max(1, stat["total"]), 3)
    
    # 分工具统计
    tool_stats = {}
    for case, result in zip(cases, results):
        if case.expected_tool:
            tool = case.expected_tool
            if tool not in tool_stats:
                tool_stats[tool] = {"total": 0, "passed": 0}
            tool_stats[tool]["total"] += 1
            tool_stats[tool]["passed"] += int(result.passed)
    
    # 添加准确率
    for tool, stat in tool_stats.items():
        stat["accuracy"] = round(stat["passed"] / max(1, stat["total"]), 3)
    
    # 延迟统计
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    latencies.sort()
    
    if latencies:
        avg_latency = round(sum(latencies) / len(latencies), 2)
        p50_latency = latencies[int(0.50 * (len(latencies) - 1))]
        p95_latency = latencies[int(0.95 * (len(latencies) - 1))]
        p99_latency = latencies[int(0.99 * (len(latencies) - 1))]
    else:
        avg_latency = p50_latency = p95_latency = p99_latency = None
    
    # 失败分析
    failure_reasons = {}
    for case, result in zip(cases, results):
        if not result.passed:
            if result.error:
                reason = "exception"
            elif case.category == "工具调用":
                if result.got_mode != "tool_call":
                    reason = "wrong_mode"
                elif result.got_tool != case.expected_tool:
                    reason = "wrong_tool"
                elif result.tool_status not in {"ok", "missing_slots"}:
                    reason = "tool_failed"
                else:
                    reason = "other"
            elif case.category == "拒识":
                reason = "reject_failed"
            else:
                reason = "other"
            
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "accuracy": round(passed / max(1, total), 3),
        "total_time_sec": round(total_time, 2),
        "avg_time_per_case_sec": round(total_time / max(1, total), 2),
        "category_stats": category_stats,
        "tool_stats": tool_stats,
        "latency": {
            "avg_ms": avg_latency,
            "p50_ms": p50_latency,
            "p95_ms": p95_latency,
            "p99_ms": p99_latency,
        },
        "failure_reasons": failure_reasons,
    }


def save_reports(out_dir: Path, results: list[TestResult], stats: dict):
    """保存报告"""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 保存详细结果CSV（包含trace）
    csv_path = out_dir / "results.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sample_id", "query", "expected_tool", "expected_behavior",
            "got_tool", "got_mode", "tool_status", "tool_provider",
            "fallback_chain", "latency_ms", "passed", "error", "trace"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "sample_id": r.sample_id,
                "query": r.query,
                "expected_tool": r.expected_tool or "",
                "expected_behavior": r.expected_behavior or "",
                "got_tool": r.got_tool or "",
                "got_mode": r.got_mode or "",
                "tool_status": r.tool_status or "",
                "tool_provider": r.tool_provider or "",
                "fallback_chain": json.dumps(r.fallback_chain, ensure_ascii=False),
                "latency_ms": r.latency_ms or "",
                "passed": r.passed,
                "error": r.error or "",
                "trace": json.dumps(r.trace, ensure_ascii=False) if r.trace else "",
            })
    
    # 2. 保存统计JSON
    json_path = out_dir / "statistics.json"
    json_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # 3. 保存失败case
    failures = [r for r in results if not r.passed]
    if failures:
        fail_csv = out_dir / "failures.csv"
        with fail_csv.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "sample_id", "query", "expected_tool", "got_tool", "got_mode",
                "tool_status", "error", "trace"
            ])
            writer.writeheader()
            for r in failures:
                writer.writerow({
                    "sample_id": r.sample_id,
                    "query": r.query,
                    "expected_tool": r.expected_tool or "",
                    "got_tool": r.got_tool or "",
                    "got_mode": r.got_mode or "",
                    "tool_status": r.tool_status or "",
                    "error": r.error or "",
                    "trace": json.dumps(r.trace, ensure_ascii=False) if r.trace else "",
                })
    
    print(f"\n{'='*60}")
    print(f"Reports saved to: {out_dir}")
    print(f"  - results.csv: {len(results)} rows")
    print(f"  - statistics.json: summary stats")
    print(f"  - failures.csv: {len(failures)} failures")
    print(f"{'='*60}\n")


def print_summary(stats: dict):
    """打印摘要"""
    print(f"\n{'='*60}")
    print(f"EVALUATION SUMMARY")
    print(f"{'='*60}\n")
    
    print(f"Overall:")
    print(f"  Total: {stats['total']}")
    print(f"  Passed: {stats['passed']} ({stats['accuracy']*100:.1f}%)")
    print(f"  Failed: {stats['failed']} ({(1-stats['accuracy'])*100:.1f}%)")
    print(f"  Time: {stats['total_time_sec']:.1f}s ({stats['avg_time_per_case_sec']:.2f}s/case)")
    
    print(f"\nBy Category:")
    for cat, stat in stats["category_stats"].items():
        print(f"  {cat}: {stat['passed']}/{stat['total']} ({stat['accuracy']*100:.1f}%)")
    
    print(f"\nBy Tool:")
    for tool, stat in sorted(stats["tool_stats"].items()):
        print(f"  {tool}: {stat['passed']}/{stat['total']} ({stat['accuracy']*100:.1f}%)")
    
    lat = stats["latency"]
    if lat["avg_ms"]:
        print(f"\nLatency:")
        print(f"  Avg: {lat['avg_ms']}ms")
        print(f"  P50: {lat['p50_ms']}ms")
        print(f"  P95: {lat['p95_ms']}ms")
        print(f"  P99: {lat['p99_ms']}ms")
    
    if stats["failure_reasons"]:
        print(f"\nFailure Reasons:")
        for reason, count in sorted(stats["failure_reasons"].items(), key=lambda x: -x[1]):
            pct = count / stats["failed"] * 100
            print(f"  {reason}: {count} ({pct:.1f}%)")
    
    print(f"\n{'='*60}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full evaluation")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8011",
        help="Base URL of the agent service"
    )
    parser.add_argument(
        "--csv",
        default="archive/csv_data/testset_eval_1000_v3.csv",
        help="Path to CSV test data"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=800,
        help="Maximum number of test cases to run"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout for each API call (seconds)"
    )
    parser.add_argument(
        "--out-dir",
        default="",
        help="Output directory for reports"
    )
    args = parser.parse_args()
    
    # 设置输出目录
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_dir = Path("eval/reports") / f"full_eval_{ts}"
    
    # 运行评测
    stats = run_evaluation(
        base_url=args.base_url,
        csv_path=Path(args.csv),
        limit=args.limit,
        timeout=args.timeout,
        out_dir=out_dir
    )
    
    # 打印摘要
    print_summary(stats)
    
    # 返回状态码
    return 0 if stats["accuracy"] >= 0.85 else 1


if __name__ == "__main__":
    raise SystemExit(main())
