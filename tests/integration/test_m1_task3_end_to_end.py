"""
M1 任务3: 工具返回质量端到端测试

目标: 验证简化方案的完整链路效果
- 从 query 到真实 POI 返回
- 统计工具返回有效率
- 验证简化方案 vs 旧方案的准确率
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.mcp_gateway import MCPToolGateway


def load_nearby_queries(csv_path: str, max_queries: int = 58) -> list[dict]:
    """加载周边推荐类query"""
    queries = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['scenario'] == 'realtime_nearby':
                queries.append({
                    'id': row['sample_id'],
                    'query': row['query'],
                })
                if len(queries) >= max_queries:
                    break
    
    return queries


def test_end_to_end():
    """端到端测试：从 query 到真实 POI 返回"""
    csv_path = "testset_eval_1000_v3.csv"
    queries = load_nearby_queries(csv_path, max_queries=58)
    
    print("=" * 80)
    print(f"M1 任务3: 工具返回质量端到端测试")
    print(f"测试集: {len(queries)} 条")
    print("=" * 80)
    print()
    
    gateway = MCPToolGateway()
    
    results = []
    success_count = 0
    has_pois_count = 0
    total = len(queries)
    
    for i, item in enumerate(queries, 1):
        query = item['query']
        query_id = item['id']
        
        print(f"[{i}/{total}] {query_id}: {query}")
        
        try:
            # 调用完整链路
            result, intent = gateway.invoke_with_intent("find_nearby", query)
            
            # 打印调试信息
            print(f"  Intent: city={intent.city if intent else 'N/A'}, anchor={intent.anchor_poi if intent else 'N/A'}, keyword={intent.category or intent.brand if intent else 'N/A'}")
            if intent:
                tool_args = intent.to_tool_args()
                print(f"  Tool args: {tool_args}")
            print(f"  Result: ok={result.ok}, error={result.error}")
            if result.raw:
                print(f"  Raw keys: {list(result.raw.keys())}")
            
            # 检查结果
            has_pois = False
            poi_count = 0
            
            if result.ok and result.raw and 'pois' in result.raw:
                pois = result.raw['pois']
                poi_count = len(pois)
                has_pois = poi_count > 0
                
                if has_pois:
                    has_pois_count += 1
                    success_count += 1
                    print(f"  ✅ 成功: 返回 {poi_count} 个 POI")
                    # 打印前3个POI
                    for j, poi in enumerate(pois[:3], 1):
                        print(f"    {j}. {poi.get('name', 'N/A')} - {poi.get('address', 'N/A')}")
                else:
                    print(f"  ⚠️  返回空: pois=[]")
            else:
                print(f"  ❌ 失败: {result.error if not result.ok else 'no pois in raw'}")
            
            results.append({
                'id': query_id,
                'query': query,
                'ok': result.ok,
                'has_pois': has_pois,
                'poi_count': poi_count,
                'error': result.error if not result.ok else None,
                'intent': intent.to_dict() if intent else None,
                'keyword': result.raw.get('keyword') if result.raw else None,
                'city': result.raw.get('city') if result.raw else None,
            })
            
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            results.append({
                'id': query_id,
                'query': query,
                'ok': False,
                'has_pois': False,
                'poi_count': 0,
                'error': str(e),
                'intent': None,
                'keyword': None,
                'city': None,
            })
        
        print()
    
    # 统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    print(f"工具调用成功率: {success_count}/{total} = {success_count/total*100:.1f}%")
    print(f"返回有效 POI 率: {has_pois_count}/{total} = {has_pois_count/total*100:.1f}%")
    
    # 失败案例分析
    print()
    print("=" * 80)
    print("失败案例分析")
    print("=" * 80)
    
    failures = [r for r in results if not r['has_pois']]
    print(f"失败总数: {len(failures)}")
    
    # 按错误类型分类
    error_types = {}
    for r in failures:
        error = r['error'] or 'no_pois'
        if error not in error_types:
            error_types[error] = []
        error_types[error].append(r)
    
    for error_type, cases in error_types.items():
        print(f"\n{error_type}: {len(cases)} 例")
        for r in cases[:5]:
            print(f"  - {r['id']}: {r['query']}")
            if r['intent']:
                print(f"    city={r['intent'].get('city')}, keyword={r['keyword']}")
    
    # 生成报告
    generate_report(results, success_count, has_pois_count, total, error_types)
    
    # 关闭 gateway
    gateway.close()
    
    return results


def generate_report(results, success_count, has_pois_count, total, error_types):
    """生成测试报告"""
    report_path = "tests/integration/m1_task3_end_to_end_report.md"
    
    report = f"""# M1 任务3: 工具返回质量端到端测试报告

**测试日期**: 2026-03-05  
**测试集**: testset_eval_1000_v3.csv (58条)  
**简化方案**: 单次 API 调用（拼接 location + keyword）

---

## 一、总体结果

| 指标 | 数量 | 总数 | 准确率 |
|------|------|------|--------|
| 工具调用成功 | {success_count} | {total} | {success_count/total*100:.1f}% |
| 返回有效 POI | {has_pois_count} | {total} | {has_pois_count/total*100:.1f}% |

---

## 二、失败案例分析

### 2.1 按错误类型分类

"""
    
    for error_type, cases in error_types.items():
        report += f"**{error_type}**: {len(cases)} 例\n\n"
        for r in cases[:10]:
            report += f"- **{r['id']}**: {r['query']}\n"
            if r['intent']:
                report += f"  - city={r['intent'].get('city')}, keyword={r['keyword']}\n"
            report += "\n"
    
    report += """
---

## 三、成功案例示例

"""
    
    successes = [r for r in results if r['has_pois']][:10]
    for r in successes:
        report += f"- **{r['id']}**: {r['query']}\n"
        report += f"  - 返回 {r['poi_count']} 个 POI\n"
        report += f"  - city={r['city']}, keyword={r['keyword']}\n\n"
    
    report += f"""
---

## 四、结论

### 4.1 简化方案有效性

- 工具返回有效率: {has_pois_count/total*100:.1f}%
- 目标: ≥ 80%
- 状态: {'✅ 达标' if has_pois_count/total >= 0.8 else '❌ 未达标'}

### 4.2 下一步

"""
    
    if has_pois_count/total >= 0.8:
        report += """
✅ 简化方案验证通过，可以继续 M1 任务4（结果重排序和格式化）
"""
    else:
        report += f"""
❌ 简化方案未达标，需要分析失败原因：
- 失败率: {(total - has_pois_count)/total*100:.1f}%
- 主要失败类型: {list(error_types.keys())}
- 建议: 分析失败案例，优化 keyword 提取或考虑回滚
"""
    
    report += """
---

**生成时间**: 2026-03-05  
**测试状态**: 完成
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已生成: {report_path}")


if __name__ == "__main__":
    test_end_to_end()
