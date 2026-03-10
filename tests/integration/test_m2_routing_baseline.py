"""
M2 路由优化基线测试

测试当前路由逻辑的准确率，为优化提供基线数据
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from domain.intents.router import route_query


# 测试集：50条查询，覆盖各种场景
TEST_CASES = [
    # === web_search 场景（20条）===
    # 人物查询
    {"query": "五条人乐队的成员都有谁", "expected": "web_search", "category": "人物"},
    {"query": "谁是马斯克", "expected": "web_search", "category": "人物"},
    {"query": "刘德华的电影有哪些", "expected": "web_search", "category": "人物"},
    
    # 地点信息查询
    {"query": "查询一下格里菲斯天文台在哪个具体位置", "expected": "web_search", "category": "地点信息"},
    {"query": "埃菲尔铁塔的高度是多少", "expected": "web_search", "category": "地点信息"},
    
    # 体育赛事
    {"query": "查询一下洛杉矶湖人队最近的比赛情况", "expected": "web_search", "category": "体育"},
    {"query": "世界杯什么时候举办", "expected": "web_search", "category": "体育"},
    {"query": "NBA总决赛赛程", "expected": "web_search", "category": "体育"},
    
    # 产品信息
    {"query": "iPhone 15 价格", "expected": "web_search", "category": "产品"},
    {"query": "特斯拉Model 3怎么样", "expected": "web_search", "category": "产品"},
    {"query": "华为Mate 60评价", "expected": "web_search", "category": "产品"},
    
    # 百科知识
    {"query": "什么是量子计算", "expected": "web_search", "category": "百科"},
    {"query": "人工智能的发展历史", "expected": "web_search", "category": "百科"},
    
    # 官网查询
    {"query": "苹果官网", "expected": "web_search", "category": "官网"},
    {"query": "搜一下特斯拉官方网站", "expected": "web_search", "category": "官网"},
    
    # 教程/文档
    {"query": "Python教程", "expected": "web_search", "category": "教程"},
    {"query": "React文档", "expected": "web_search", "category": "教程"},
    
    # 新闻/资讯
    {"query": "最新科技新闻", "expected": "web_search", "category": "新闻"},
    {"query": "今天的头条", "expected": "web_search", "category": "新闻"},
    {"query": "苹果发布会", "expected": "web_search", "category": "新闻"},
    
    # === find_nearby 场景（15条）===
    {"query": "北京国贸附近的咖啡厅", "expected": "find_nearby", "category": "location"},
    {"query": "上海静安寺周边的餐厅", "expected": "find_nearby", "category": "location"},
    {"query": "深圳南山哪里有加油站", "expected": "find_nearby", "category": "location"},
    {"query": "广州天河城附近的停车场", "expected": "find_nearby", "category": "location"},
    {"query": "杭州西湖周边的酒店", "expected": "find_nearby", "category": "location"},
    {"query": "成都春熙路附近有什么好吃的", "expected": "find_nearby", "category": "location"},
    {"query": "武汉光谷哪里有电影院", "expected": "find_nearby", "category": "location"},
    {"query": "南京新街口附近的KTV", "expected": "find_nearby", "category": "location"},
    {"query": "西安小寨周边的超市", "expected": "find_nearby", "category": "location"},
    {"query": "重庆解放碑附近的便利店", "expected": "find_nearby", "category": "location"},
    {"query": "最近的星巴克", "expected": "find_nearby", "category": "location"},
    {"query": "离我最近的加油站", "expected": "find_nearby", "category": "location"},
    {"query": "附近有没有711", "expected": "find_nearby", "category": "location"},
    {"query": "周边的医院", "expected": "find_nearby", "category": "location"},
    {"query": "这附近哪里有药店", "expected": "find_nearby", "category": "location"},
    
    # === 边界case（15条）===
    # 地点 + 信息查询（应该是 web_search）
    {"query": "北京国贸有什么好玩的景点", "expected": "web_search", "category": "边界-景点推荐"},
    {"query": "上海外滩的历史", "expected": "web_search", "category": "边界-历史"},
    {"query": "杭州西湖的传说", "expected": "web_search", "category": "边界-文化"},
    
    # 品牌 + 信息查询（应该是 web_search）
    {"query": "星巴克的创始人是谁", "expected": "web_search", "category": "边界-品牌"},
    {"query": "麦当劳的历史", "expected": "web_search", "category": "边界-品牌"},
    
    # 城市 + 体育（应该是 web_search，不是 find_nearby）
    {"query": "洛杉矶湖人队的主场在哪", "expected": "web_search", "category": "边界-体育"},
    {"query": "北京国安的比赛时间", "expected": "web_search", "category": "边界-体育"},
    
    # 模糊地点查询（应该是 find_nearby）
    {"query": "附近有什么好吃的", "expected": "find_nearby", "category": "边界-模糊"},
    {"query": "周边有什么好玩的", "expected": "find_nearby", "category": "边界-模糊"},
    {"query": "这里有什么推荐的", "expected": "find_nearby", "category": "边界-模糊"},
    
    # 闲聊（应该是 reply）
    {"query": "你好", "expected": "reply", "category": "闲聊"},
    {"query": "今天天气真好", "expected": "reply", "category": "闲聊"},
    {"query": "谢谢", "expected": "reply", "category": "闲聊"},
    {"query": "再见", "expected": "reply", "category": "闲聊"},
    {"query": "你是谁", "expected": "reply", "category": "闲聊"},
]


def test_routing_baseline():
    """测试路由基线准确率"""
    print("=" * 80)
    print("M2 路由优化基线测试")
    print("=" * 80)
    print()
    
    results = []
    correct = 0
    total = len(TEST_CASES)
    
    # 按类别统计
    category_stats = {}
    
    for i, case in enumerate(TEST_CASES, 1):
        query = case['query']
        expected = case['expected']
        category = case['category']
        
        # 调用路由逻辑
        decision = route_query(query)
        actual = decision.tool_name if decision.tool_name else decision.decision_mode
        
        is_correct = actual == expected
        if is_correct:
            correct += 1
        
        # 统计
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'correct': 0}
        category_stats[category]['total'] += 1
        if is_correct:
            category_stats[category]['correct'] += 1
        
        # 打印结果
        status = "✅" if is_correct else "❌"
        print(f"[{i}/{total}] {status} {query}")
        print(f"  期望: {expected}, 实际: {actual}, 类别: {category}")
        if not is_correct:
            print(f"  ⚠️ 路由错误")
        print()
        
        results.append({
            'query': query,
            'expected': expected,
            'actual': actual,
            'category': category,
            'correct': is_correct,
        })
    
    # 总体统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    accuracy = correct / total * 100
    print(f"总查询数: {total}")
    print(f"正确数: {correct}")
    print(f"准确率: {accuracy:.1f}%")
    print()
    
    # 按类别统计
    print("按类别统计:")
    for category, stats in sorted(category_stats.items()):
        cat_accuracy = stats['correct'] / stats['total'] * 100
        print(f"  {category}: {stats['correct']}/{stats['total']} ({cat_accuracy:.1f}%)")
    print()
    
    # 失败case分析
    failed_cases = [r for r in results if not r['correct']]
    if failed_cases:
        print("=" * 80)
        print(f"失败Case分析（{len(failed_cases)}条）")
        print("=" * 80)
        for case in failed_cases:
            print(f"Query: {case['query']}")
            print(f"  期望: {case['expected']}, 实际: {case['actual']}, 类别: {case['category']}")
        print()
    
    # 生成报告
    generate_report(results, correct, total, category_stats)
    
    return accuracy


def generate_report(results, correct, total, category_stats):
    """生成测试报告"""
    report_path = "tests/integration/m2_routing_baseline_report.md"
    
    accuracy = correct / total * 100
    
    report = f"""# M2 路由优化基线测试报告

**测试日期**: 2026-03-05  
**测试目标**: 评估当前路由逻辑的准确率

---

## 一、总体结果

| 指标 | 数值 |
|------|------|
| 总查询数 | {total} |
| 正确数 | {correct} |
| 准确率 | {accuracy:.1f}% |

**M2 目标**: ≥ 95%  
**当前状态**: {'✅ 达标' if accuracy >= 95 else '❌ 未达标'}

---

## 二、按类别统计

"""
    
    for category, stats in sorted(category_stats.items()):
        cat_accuracy = stats['correct'] / stats['total'] * 100
        report += f"### {category}\n\n"
        report += f"- 查询数: {stats['total']}\n"
        report += f"- 正确数: {stats['correct']}\n"
        report += f"- 准确率: {cat_accuracy:.1f}%\n\n"
    
    # 失败case
    failed_cases = [r for r in results if not r['correct']]
    if failed_cases:
        report += f"""---

## 三、失败Case分析（{len(failed_cases)}条）

"""
        for i, case in enumerate(failed_cases, 1):
            report += f"### Case {i}: {case['query']}\n\n"
            report += f"- 期望工具: {case['expected']}\n"
            report += f"- 实际工具: {case['actual']}\n"
            report += f"- 类别: {case['category']}\n\n"
    
    report += """---

## 四、优化建议

基于失败case分析，建议：

1. 扩展 web_search 关键词覆盖
2. 添加排除规则防止误路由
3. 提高 web_search 优先级

---

**生成时间**: 2026-03-05  
**下一步**: 实施路由优化
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已生成: {report_path}")


if __name__ == "__main__":
    accuracy = test_routing_baseline()
    print(f"\n最终准确率: {accuracy:.1f}%")
    print(f"M2 目标: ≥ 95%")
    print(f"状态: {'✅ 达标' if accuracy >= 95 else '❌ 未达标'}")
