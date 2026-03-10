"""
M2 任务2：Query 预处理测试

测试 Query 预处理的效果，包括停用词去除、关键词提取、Query 重写
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from domain.tools.query_preprocessor import preprocess_web_search_query


# 测试集：30条查询，覆盖各种场景
TEST_CASES = [
    # === 停用词去除测试（10条）===
    {
        "query": "帮我查一下iPhone 15的价格",
        "expected_keywords": ["iPhone", "15", "价格"],
        "category": "停用词-帮我查",
    },
    {
        "query": "请问特斯拉Model 3怎么样",
        "expected_keywords": ["特斯拉", "Model", "3", "怎么样"],
        "category": "停用词-请问",
    },
    {
        "query": "我想知道华为Mate 60的评价",
        "expected_keywords": ["华为", "Mate", "60", "评价"],
        "category": "停用词-我想知道",
    },
    {
        "query": "告诉我五条人乐队的成员都有谁",
        "expected_keywords": ["五条人", "乐队", "成员"],
        "category": "停用词-告诉我",
    },
    {
        "query": "搜索一下格里菲斯天文台在哪个具体位置",
        "expected_keywords": ["格里菲斯", "天文台", "位置"],
        "category": "停用词-搜索一下",
    },
    {
        "query": "查询一下洛杉矶湖人队最近的比赛情况",
        "expected_keywords": ["洛杉矶", "湖人队", "比赛"],
        "category": "停用词-查询一下",
    },
    {
        "query": "看看Python教程有哪些",
        "expected_keywords": ["Python", "教程"],
        "category": "停用词-看看",
    },
    {
        "query": "了解一下量子计算是什么",
        "expected_keywords": ["量子计算"],
        "category": "停用词-了解一下",
    },
    {
        "query": "给我推荐一些React文档",
        "expected_keywords": ["React", "文档", "推荐"],
        "category": "停用词-给我",
    },
    {
        "query": "能不能告诉我苹果发布会的时间",
        "expected_keywords": ["苹果", "发布会", "时间"],
        "category": "停用词-能不能",
    },
    
    # === 长Query重写测试（10条）===
    {
        "query": "我想了解一下最近有什么关于人工智能的最新发展和技术突破",
        "expected_keywords": ["人工智能", "发展", "技术", "突破"],
        "category": "长Query",
    },
    {
        "query": "请帮我查询一下北京到上海的高铁票价格和时刻表信息",
        "expected_keywords": ["北京", "上海", "高铁", "票价", "时刻表"],
        "category": "长Query",
    },
    {
        "query": "能不能给我介绍一下特斯拉公司的创始人马斯克的个人经历和成就",
        "expected_keywords": ["特斯拉", "马斯克", "经历", "成就"],
        "category": "长Query",
    },
    {
        "query": "我想知道最近有没有什么好看的电影推荐，最好是科幻类型的",
        "expected_keywords": ["电影", "推荐", "科幻"],
        "category": "长Query",
    },
    {
        "query": "请问一下杭州西湖的历史文化背景和著名景点有哪些",
        "expected_keywords": ["杭州", "西湖", "历史", "景点"],
        "category": "长Query",
    },
    {
        "query": "帮我搜索一下关于量子计算机的工作原理和应用场景的详细资料",
        "expected_keywords": ["量子计算机", "原理", "应用"],
        "category": "长Query",
    },
    {
        "query": "我想了解一下最新的iPhone 15 Pro Max的配置参数和价格信息",
        "expected_keywords": ["iPhone", "15", "Pro", "Max", "配置", "价格"],
        "category": "长Query",
    },
    {
        "query": "能不能告诉我世界杯足球赛的历史和最近一届的比赛结果",
        "expected_keywords": ["世界杯", "历史", "比赛"],
        "category": "长Query",
    },
    {
        "query": "请帮我查一下关于区块链技术的基本概念和实际应用案例",
        "expected_keywords": ["区块链", "概念", "应用"],
        "category": "长Query",
    },
    {
        "query": "我想知道最近有什么关于新能源汽车行业的政策和市场动态",
        "expected_keywords": ["新能源", "汽车", "政策", "市场"],
        "category": "长Query",
    },
    
    # === 口语化Query测试（10条）===
    {
        "query": "iPhone 15多少钱啊",
        "expected_keywords": ["iPhone", "15", "多少钱"],
        "category": "口语化-啊",
    },
    {
        "query": "特斯拉咋样呢",
        "expected_keywords": ["特斯拉", "咋样"],
        "category": "口语化-呢",
    },
    {
        "query": "华为手机好不好用呀",
        "expected_keywords": ["华为", "手机", "好用"],
        "category": "口语化-呀",
    },
    {
        "query": "这个电影好看吗",
        "expected_keywords": ["电影", "好看"],
        "category": "口语化-吗",
    },
    {
        "query": "Python难学不难学",
        "expected_keywords": ["Python", "难学"],
        "category": "口语化-重复",
    },
    {
        "query": "量子计算是啥玩意儿",
        "expected_keywords": ["量子计算"],
        "category": "口语化-啥玩意儿",
    },
    {
        "query": "React框架咋用啊",
        "expected_keywords": ["React", "框架", "咋用"],
        "category": "口语化-咋用",
    },
    {
        "query": "苹果发布会啥时候开",
        "expected_keywords": ["苹果", "发布会", "时候"],
        "category": "口语化-啥时候",
    },
    {
        "query": "这个东西在哪买得到",
        "expected_keywords": ["东西", "哪买"],
        "category": "口语化-得到",
    },
    {
        "query": "马斯克是干啥的",
        "expected_keywords": ["马斯克", "干啥"],
        "category": "口语化-干啥",
    },
]


def test_query_preprocessing():
    """测试 Query 预处理效果"""
    print("=" * 80)
    print("M2 任务2：Query 预处理测试")
    print("=" * 80)
    print()
    
    results = []
    total = len(TEST_CASES)
    
    # 按类别统计
    category_stats = {}
    
    for i, case in enumerate(TEST_CASES, 1):
        query = case['query']
        expected_keywords = case['expected_keywords']
        category = case['category']
        
        # 调用预处理
        result = preprocess_web_search_query(query)
        normalized = result['normalized_query']
        keywords = result['keywords']
        
        # 评估：检查期望关键词是否被提取
        extracted_keywords = set(keywords)
        expected_set = set(expected_keywords)
        
        # 计算召回率（期望关键词中有多少被提取）
        matched = len(expected_set & extracted_keywords)
        recall = matched / len(expected_set) if expected_set else 0
        
        # 统计
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'recall_sum': 0}
        category_stats[category]['total'] += 1
        category_stats[category]['recall_sum'] += recall
        
        # 打印结果
        status = "✅" if recall >= 0.6 else "❌"
        print(f"[{i}/{total}] {status} {query}")
        print(f"  原始: {query}")
        print(f"  标准化: {normalized}")
        print(f"  提取关键词: {keywords}")
        print(f"  期望关键词: {expected_keywords}")
        print(f"  召回率: {recall*100:.1f}% ({matched}/{len(expected_set)})")
        print()
        
        results.append({
            'query': query,
            'normalized': normalized,
            'keywords': keywords,
            'expected_keywords': expected_keywords,
            'recall': recall,
            'category': category,
        })
    
    # 总体统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    avg_recall = sum(r['recall'] for r in results) / total * 100
    print(f"总查询数: {total}")
    print(f"平均召回率: {avg_recall:.1f}%")
    print()
    
    # 按类别统计
    print("按类别统计:")
    for category, stats in sorted(category_stats.items()):
        cat_recall = stats['recall_sum'] / stats['total'] * 100
        print(f"  {category}: {cat_recall:.1f}%")
    print()
    
    # 生成报告
    generate_report(results, category_stats)
    
    return avg_recall


def generate_report(results, category_stats):
    """生成测试报告"""
    report_path = "tests/integration/m2_query_preprocessing_report.md"
    
    total = len(results)
    avg_recall = sum(r['recall'] for r in results) / total * 100
    
    report = f"""# M2 Query 预处理测试报告

**测试日期**: 2026-03-05  
**测试目标**: 评估 Query 预处理的效果

---

## 一、总体结果

| 指标 | 数值 |
|------|------|
| 总查询数 | {total} |
| 平均召回率 | {avg_recall:.1f}% |

**M2 目标**: ≥ 80%  
**当前状态**: {'✅ 达标' if avg_recall >= 80 else '❌ 未达标'}

---

## 二、按类别统计

"""
    
    for category, stats in sorted(category_stats.items()):
        cat_recall = stats['recall_sum'] / stats['total'] * 100
        report += f"### {category}\n\n"
        report += f"- 查询数: {stats['total']}\n"
        report += f"- 平均召回率: {cat_recall:.1f}%\n\n"
    
    report += """---

## 三、优化建议

基于测试结果，建议：

1. 扩展停用词列表（口语化词汇）
2. 优化关键词提取算法
3. 添加 Query 重写规则（长→短）

---

**生成时间**: 2026-03-05  
**下一步**: 实施优化
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已生成: {report_path}")


if __name__ == "__main__":
    recall = test_query_preprocessing()
    print(f"\n平均召回率: {recall:.1f}%")
    print(f"M2 目标: ≥ 80%")
    print(f"状态: {'✅ 达标' if recall >= 80 else '❌ 未达标'}")
