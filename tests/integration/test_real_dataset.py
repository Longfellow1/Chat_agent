"""
测试真实数据集（过滤掉无地理位置的query）
"""
import csv
import sys
import os
from pathlib import Path

# Add agent_service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from app.factory import build_flow
from app.schemas.contracts import ChatRequest


def should_skip_query(query: str) -> bool:
    """判断是否应该跳过该query（无地理位置信息）"""
    q = query.lower().strip()
    
    # 跳过以"附近"、"周边"开头且无其他地理信息的query
    nearby_patterns = ["附近", "周边", "这附近", "那附近", "我附近"]
    
    for pattern in nearby_patterns:
        if pattern in q:
            # 检查是否有明确的地理位置信息
            # 如果有城市名、地标名等，则不跳过
            has_location = any(loc in q for loc in [
                "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "成都", "重庆", "武汉",
                "西安", "郑州", "天津", "长沙", "青岛", "济南", "合肥", "南昌", "福州", "厦门",
                "海底捞", "静安寺", "外滩", "西湖", "鸟巢", "天安门", "故宫", "长城",
                "新街口", "西街口", "佛山", "顺德", "临平", "中铁逸都"
            ])
            
            if not has_location:
                return True
    
    return False


def load_queries(csv_path: str, max_queries: int = 100) -> list[str]:
    """加载CSV文件中的query"""
    queries = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row['question'].strip()
            if query and not should_skip_query(query):
                queries.append(query)
                if len(queries) >= max_queries:
                    break
    
    return queries


def test_queries(queries: list[str]):
    """测试queries并生成报告"""
    flow = build_flow()
    
    results = []
    tool_distribution = {}
    decision_distribution = {}
    
    for i, query in enumerate(queries, 1):
        try:
            req = ChatRequest(query=query, session_id=f"test_{i}")
            resp = flow.run(req)
            
            result = {
                "query": query,
                "decision_mode": resp.decision_mode,
                "tool_name": resp.tool_name,
                "route_source": resp.route_source,
                "tool_status": resp.tool_status,
                "response": resp.final_text[:100] if resp.final_text else ""
            }
            results.append(result)
            
            # 统计
            tool_distribution[resp.tool_name or "none"] = tool_distribution.get(resp.tool_name or "none", 0) + 1
            decision_distribution[resp.decision_mode] = decision_distribution.get(resp.decision_mode, 0) + 1
            
            print(f"[{i}/{len(queries)}] {query[:50]}... → {resp.decision_mode}/{resp.tool_name}")
            
        except Exception as e:
            print(f"[{i}/{len(queries)}] ERROR: {query[:50]}... → {str(e)}")
            results.append({
                "query": query,
                "decision_mode": "error",
                "tool_name": None,
                "route_source": None,
                "tool_status": None,
                "response": str(e)
            })
    
    return results, tool_distribution, decision_distribution


def generate_report(results: list[dict], tool_dist: dict, decision_dist: dict, output_path: str):
    """生成测试报告"""
    total = len(results)
    
    report = f"""# 真实数据集测试报告（过滤无地理位置query）

## 测试概览

- 总query数: {total}
- 测试时间: 2026-03-04

## Decision Mode 分布

| Decision Mode | 数量 | 占比 |
|--------------|------|------|
"""
    
    for mode, count in sorted(decision_dist.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        report += f"| {mode} | {count} | {pct:.1f}% |\n"
    
    report += f"""
## Tool 分布

| Tool Name | 数量 | 占比 |
|-----------|------|------|
"""
    
    for tool, count in sorted(tool_dist.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        report += f"| {tool} | {count} | {pct:.1f}% |\n"
    
    report += "\n## 详细结果\n\n"
    
    # 按tool分组
    by_tool = {}
    for r in results:
        tool = r["tool_name"] or "none"
        if tool not in by_tool:
            by_tool[tool] = []
        by_tool[tool].append(r)
    
    for tool, queries in sorted(by_tool.items(), key=lambda x: -len(x[1])):
        report += f"\n### {tool} ({len(queries)}条)\n\n"
        for r in queries[:20]:  # 每个tool最多显示20条
            report += f"- **Query**: {r['query']}\n"
            report += f"  - Decision: {r['decision_mode']}\n"
            report += f"  - Route: {r['route_source']}\n"
            report += f"  - Status: {r['tool_status']}\n"
            if r['response']:
                report += f"  - Response: {r['response']}\n"
            report += "\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已生成: {output_path}")


if __name__ == "__main__":
    # 测试数据集路径
    datasets = [
        "/Users/Harland/Documents/Data_analysis/chat_evaluation/output/test_datasets/周边推荐_核心测试集.csv",
        "/Users/Harland/Documents/Data_analysis/chat_evaluation/output/test_datasets/设施查询_补充测试集.csv",
        "/Users/Harland/Documents/Data_analysis/chat_evaluation/output/test_datasets/行程规划_扩展场景.csv",
        "/Users/Harland/Documents/Data_analysis/chat_evaluation/output/test_datasets/其他服务_边界case.csv",
    ]
    
    all_queries = []
    for dataset in datasets:
        if os.path.exists(dataset):
            queries = load_queries(dataset, max_queries=50)  # 每个数据集最多50条
            all_queries.extend(queries)
            print(f"从 {os.path.basename(dataset)} 加载了 {len(queries)} 条query")
    
    print(f"\n总共加载 {len(all_queries)} 条query（已过滤无地理位置query）\n")
    
    if all_queries:
        results, tool_dist, decision_dist = test_queries(all_queries)
        
        output_path = "tests/integration/real_dataset_test_report.md"
        generate_report(results, tool_dist, decision_dist, output_path)
