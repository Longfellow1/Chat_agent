"""
测试周边推荐场景（从testset_eval_1000_v3.csv抽取）
"""
import csv
import sys
from pathlib import Path

# Add agent_service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from app.factory import build_flow
from app.schemas.contracts import ChatRequest


def load_nearby_queries(csv_path: str, max_queries: int = 100) -> list[dict]:
    """加载周边推荐类query"""
    queries = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:  # Handle BOM
        reader = csv.DictReader(f)
        for row in reader:
            # 只选择realtime_nearby场景
            if row['scenario'] == 'realtime_nearby':
                queries.append({
                    'id': row['sample_id'],
                    'query': row['query'],
                    'expected_tool': row['expected_tool'],
                    'expected_behavior': row['expected_behavior'],
                })
                if len(queries) >= max_queries:
                    break
    
    return queries


def test_queries(queries: list[dict]):
    """测试queries并生成报告"""
    flow = build_flow()
    
    results = []
    correct = 0
    wrong_tool = 0
    wrong_decision = 0
    
    for i, item in enumerate(queries, 1):
        query = item['query']
        expected_tool = item['expected_tool']
        expected_behavior = item['expected_behavior']
        
        try:
            req = ChatRequest(query=query, session_id=f"test_{i}")
            resp = flow.run(req)
            
            # 判断是否正确
            is_correct = False
            error_type = None
            
            if expected_behavior == 'tool_call_then_nearby':
                if resp.decision_mode == 'tool_call' and resp.tool_name == 'find_nearby':
                    is_correct = True
                    correct += 1
                elif resp.decision_mode != 'tool_call':
                    error_type = 'wrong_decision'
                    wrong_decision += 1
                elif resp.tool_name != 'find_nearby':
                    error_type = 'wrong_tool'
                    wrong_tool += 1
            
            result = {
                "id": item['id'],
                "query": query,
                "expected_tool": expected_tool,
                "expected_behavior": expected_behavior,
                "actual_decision": resp.decision_mode,
                "actual_tool": resp.tool_name,
                "route_source": resp.route_source,
                "tool_status": resp.tool_status,
                "is_correct": is_correct,
                "error_type": error_type,
                "response": resp.final_text if resp.final_text else ""
            }
            results.append(result)
            
            status = "✓" if is_correct else "✗"
            print(f"[{i}/{len(queries)}] {status} {query[:40]}... → {resp.decision_mode}/{resp.tool_name}")
            
        except Exception as e:
            print(f"[{i}/{len(queries)}] ERROR: {query[:40]}... → {str(e)}")
            results.append({
                "id": item['id'],
                "query": query,
                "expected_tool": expected_tool,
                "expected_behavior": expected_behavior,
                "actual_decision": "error",
                "actual_tool": None,
                "route_source": None,
                "tool_status": None,
                "is_correct": False,
                "error_type": "exception",
                "response": str(e)
            })
    
    return results, correct, wrong_tool, wrong_decision


def generate_report(results: list[dict], correct: int, wrong_tool: int, wrong_decision: int, output_path: str):
    """生成测试报告"""
    total = len(results)
    accuracy = correct / total * 100 if total > 0 else 0
    
    report = f"""# 周边推荐测试报告（testset_eval_1000_v3.csv）

## 测试概览

- 总query数: {total}
- 正确数: {correct}
- 准确率: {accuracy:.1f}%
- 测试时间: 2026-03-04

## 错误分布

| 错误类型 | 数量 | 占比 |
|---------|------|------|
| 正确 | {correct} | {correct/total*100:.1f}% |
| 错误决策（非tool_call） | {wrong_decision} | {wrong_decision/total*100:.1f}% |
| 错误工具（非find_nearby） | {wrong_tool} | {wrong_tool/total*100:.1f}% |

## 错误案例分析

### 错误决策案例（非tool_call）

"""
    
    wrong_decision_cases = [r for r in results if r['error_type'] == 'wrong_decision']
    for r in wrong_decision_cases[:20]:
        report += f"- **{r['id']}**: {r['query']}\n"
        report += f"  - 期望: tool_call/find_nearby\n"
        report += f"  - 实际: {r['actual_decision']}/{r['actual_tool']}\n"
        report += f"  - Route: {r['route_source']}\n"
        report += f"  - Response: {r['response']}\n\n"
    
    report += "\n### 错误工具案例（非find_nearby）\n\n"
    
    wrong_tool_cases = [r for r in results if r['error_type'] == 'wrong_tool']
    for r in wrong_tool_cases[:20]:
        report += f"- **{r['id']}**: {r['query']}\n"
        report += f"  - 期望: tool_call/find_nearby\n"
        report += f"  - 实际: {r['actual_decision']}/{r['actual_tool']}\n"
        report += f"  - Route: {r['route_source']}\n"
        report += f"  - Response: {r['response']}\n\n"
    
    report += "\n## 正确案例（前20条）\n\n"
    
    correct_cases = [r for r in results if r['is_correct']]
    for r in correct_cases[:20]:
        report += f"- **{r['id']}**: {r['query']}\n"
        report += f"  - Decision: {r['actual_decision']}/{r['actual_tool']}\n"
        report += f"  - Route: {r['route_source']}\n"
        report += f"  - Status: {r['tool_status']}\n"
        report += f"  - Response: {r['response']}\n\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已生成: {output_path}")
    print(f"\n准确率: {accuracy:.1f}% ({correct}/{total})")


if __name__ == "__main__":
    csv_path = "testset_eval_1000_v3.csv"
    
    queries = load_nearby_queries(csv_path, max_queries=100)
    print(f"加载了 {len(queries)} 条周边推荐query\n")
    
    if queries:
        results, correct, wrong_tool, wrong_decision = test_queries(queries)
        
        output_path = "tests/integration/nearby_100_test_report.md"
        generate_report(results, correct, wrong_tool, wrong_decision, output_path)
