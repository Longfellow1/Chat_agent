"""
M2 任务3：结果排序优化测试

测试 web_search 结果的排序和过滤效果
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from infra.tool_clients.search_result_processor import SearchResultProcessor


# 测试集：20条查询，覆盖各种场景
TEST_CASES = [
    # === 新闻类（5条）===
    {
        "query": "特斯拉最新消息",
        "category": "新闻",
        "expected_features": ["时效性", "权威来源"],
    },
    {
        "query": "苹果发布会",
        "category": "新闻",
        "expected_features": ["时效性", "官方信息"],
    },
    {
        "query": "世界杯比赛结果",
        "category": "新闻",
        "expected_features": ["时效性", "体育媒体"],
    },
    {
        "query": "iPhone 15价格",
        "category": "新闻",
        "expected_features": ["时效性", "电商信息"],
    },
    {
        "query": "华为Mate 60评测",
        "category": "新闻",
        "expected_features": ["时效性", "科技媒体"],
    },
    
    # === 百科类（5条）===
    {
        "query": "量子计算原理",
        "category": "百科",
        "expected_features": ["权威来源", "深度内容"],
    },
    {
        "query": "区块链技术",
        "category": "百科",
        "expected_features": ["权威来源", "技术文档"],
    },
    {
        "query": "人工智能发展史",
        "category": "百科",
        "expected_features": ["权威来源", "历史资料"],
    },
    {
        "query": "马斯克个人经历",
        "category": "百科",
        "expected_features": ["权威来源", "人物传记"],
    },
    {
        "query": "五条人乐队成员",
        "category": "百科",
        "expected_features": ["权威来源", "音乐资料"],
    },
    
    # === 问答类（5条）===
    {
        "query": "Python怎么学",
        "category": "问答",
        "expected_features": ["实用性", "教程指南"],
    },
    {
        "query": "React框架优缺点",
        "category": "问答",
        "expected_features": ["实用性", "技术对比"],
    },
    {
        "query": "如何学习量子计算",
        "category": "问答",
        "expected_features": ["实用性", "学习路径"],
    },
    {
        "query": "特斯拉值得买吗",
        "category": "问答",
        "expected_features": ["实用性", "用户评价"],
    },
    {
        "query": "iPhone和华为哪个好",
        "category": "问答",
        "expected_features": ["实用性", "产品对比"],
    },
    
    # === 攻略类（5条）===
    {
        "query": "杭州西湖旅游攻略",
        "category": "攻略",
        "expected_features": ["实用性", "详细指南"],
    },
    {
        "query": "格里菲斯天文台游玩攻略",
        "category": "攻略",
        "expected_features": ["实用性", "景点介绍"],
    },
    {
        "query": "洛杉矶旅游景点推荐",
        "category": "攻略",
        "expected_features": ["实用性", "景点列表"],
    },
    {
        "query": "北京美食推荐",
        "category": "攻略",
        "expected_features": ["实用性", "餐厅列表"],
    },
    {
        "query": "上海购物攻略",
        "category": "攻略",
        "expected_features": ["实用性", "商场列表"],
    },
]


def test_result_ranking():
    """测试结果排序效果"""
    print("=" * 80)
    print("M2 任务3：结果排序优化测试")
    print("=" * 80)
    print()
    
    processor = SearchResultProcessor()
    
    results = []
    total = len(TEST_CASES)
    
    # 按类别统计
    category_stats = {}
    
    for i, case in enumerate(TEST_CASES, 1):
        query = case['query']
        category = case['category']
        expected_features = case['expected_features']
        
        print(f"[{i}/{total}] {query}")
        print(f"  类别: {category}")
        print(f"  期望特征: {', '.join(expected_features)}")
        
        # 模拟搜索结果（实际应该调用 Tavily）
        # 这里先测试排序逻辑
        mock_results = _generate_mock_results(query, category)
        
        # 应用排序和过滤
        ranked_results = processor.process_results(mock_results, query)
        
        # 评估排序质量
        score = _evaluate_ranking(ranked_results, expected_features)
        
        # 统计
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'score_sum': 0}
        category_stats[category]['total'] += 1
        category_stats[category]['score_sum'] += score
        
        status = "✅" if score >= 0.7 else "❌"
        print(f"  排序质量: {status} {score*100:.1f}%")
        print()
        
        results.append({
            'query': query,
            'category': category,
            'score': score,
        })
    
    # 总体统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    avg_score = sum(r['score'] for r in results) / total * 100
    print(f"总查询数: {total}")
    print(f"平均排序质量: {avg_score:.1f}%")
    print()
    
    # 按类别统计
    print("按类别统计:")
    for category, stats in sorted(category_stats.items()):
        cat_score = stats['score_sum'] / stats['total'] * 100
        print(f"  {category}: {cat_score:.1f}%")
    print()
    
    # 生成报告
    generate_report(results, category_stats)
    
    return avg_score


def _generate_mock_results(query: str, category: str) -> list[dict]:
    """生成模拟搜索结果（用于测试排序逻辑）"""
    # 实际应该调用 Tavily API
    # 这里生成模拟数据测试排序
    
    if category == "新闻":
        return [
            {
                "title": f"{query} - 新浪科技",
                "url": "https://tech.sina.com.cn",
                "content": f"最新消息：{query}...",
                "published_date": "2026-03-05",
                "score": 0.95,
            },
            {
                "title": f"{query} - 官方发布",
                "url": "https://example.com/official",
                "content": f"官方消息：{query}...",
                "published_date": "2026-03-04",
                "score": 0.90,
            },
            {
                "title": f"{query} - 知乎讨论",
                "url": "https://zhihu.com",
                "content": f"关于{query}的讨论...",
                "published_date": "2026-02-01",
                "score": 0.75,
            },
            {
                "title": f"{query} - 个人博客",
                "url": "https://blog.example.com",
                "content": f"我对{query}的看法...",
                "published_date": "2024-06-01",
                "score": 0.65,
            },
        ]
    
    elif category == "百科":
        return [
            {
                "title": f"{query} - 百度百科",
                "url": "https://baike.baidu.com",
                "content": f"{query}是指..." * 20,  # 深度内容
                "published_date": "2025-01-01",
                "score": 0.95,
            },
            {
                "title": f"{query} - 维基百科",
                "url": "https://wikipedia.org",
                "content": f"{query}（英语：...）" * 15,
                "published_date": "2024-06-01",
                "score": 0.90,
            },
            {
                "title": f"{query} - 知乎专栏",
                "url": "https://zhuanlan.zhihu.com",
                "content": f"深度解析{query}..." * 10,
                "published_date": "2026-01-01",
                "score": 0.80,
            },
            {
                "title": f"{query} - 个人博客",
                "url": "https://blog.example.com",
                "content": f"简单介绍{query}...",
                "published_date": "2023-01-01",
                "score": 0.60,
            },
        ]
    
    elif category == "问答":
        return [
            {
                "title": f"{query} - 完整教程指南",
                "url": "https://example.com/tutorial",
                "content": f"如何{query}：第一步..." * 10,
                "published_date": "2026-02-01",
                "score": 0.95,
            },
            {
                "title": f"{query} - 知乎回答",
                "url": "https://zhihu.com",
                "content": f"关于{query}的回答...",
                "published_date": "2026-01-01",
                "score": 0.85,
            },
            {
                "title": f"{query} - CSDN博客",
                "url": "https://blog.csdn.net",
                "content": f"{query}的方法...",
                "published_date": "2025-06-01",
                "score": 0.75,
            },
            {
                "title": f"{query} - 广告页面",
                "url": "https://ad.example.com",
                "content": f"购买{query}课程...",
                "published_date": "2026-03-01",
                "score": 0.55,
            },
        ]
    
    elif category == "攻略":
        return [
            {
                "title": f"{query} - 详细攻略指南",
                "url": "https://mafengwo.cn",
                "content": f"{query}完整攻略：..." * 15,
                "published_date": "2026-02-01",
                "score": 0.95,
            },
            {
                "title": f"{query} - 推荐",
                "url": "https://ctrip.com",
                "content": f"{query}推荐列表...",
                "published_date": "2026-01-01",
                "score": 0.85,
            },
            {
                "title": f"{query} - 知乎",
                "url": "https://zhihu.com",
                "content": f"关于{query}的讨论...",
                "published_date": "2025-06-01",
                "score": 0.75,
            },
            {
                "title": f"{query} - 个人游记",
                "url": "https://blog.example.com",
                "content": f"我的{query}经历...",
                "published_date": "2024-01-01",
                "score": 0.60,
            },
        ]
    
    else:
        return []


def _evaluate_ranking(results: list[dict], expected_features: list[str]) -> float:
    """评估排序质量"""
    if not results:
        return 0.0
    
    # 检查 top 3 结果是否符合期望特征
    top_3 = results[:3]
    
    score = 0.0
    max_score = len(expected_features)  # 每个特征最多 1 分
    
    for result in top_3:
        for feature in expected_features:
            # 检查时效性
            if feature == "时效性":
                if "2026" in result.get("published_date", ""):
                    score += 0.33  # 每个结果贡献 1/3 分
            
            # 检查权威来源
            elif feature == "权威来源":
                url = result.get("url", "")
                if any(domain in url for domain in ["gov", "edu", "baidu", "wikipedia"]):
                    score += 0.33
            
            # 检查官方信息
            elif feature == "官方信息":
                title = result.get("title", "")
                if "官方" in title or "official" in title.lower():
                    score += 0.33
            
            # 检查实用性
            elif feature == "实用性":
                title = result.get("title", "")
                if any(word in title for word in ["攻略", "教程", "指南", "推荐", "怎么", "如何"]):
                    score += 0.33
            
            # 检查深度内容
            elif feature == "深度内容":
                content = result.get("content", "")
                if len(content) > 100:  # 内容较长
                    score += 0.33
            
            # 检查详细指南
            elif feature == "详细指南":
                title = result.get("title", "")
                if any(word in title for word in ["攻略", "指南", "详细", "完整"]):
                    score += 0.33
    
    # 归一化到 [0, 1]
    return min(score / max_score, 1.0)


def generate_report(results, category_stats):
    """生成测试报告"""
    report_path = "tests/integration/m2_result_ranking_report.md"
    
    total = len(results)
    avg_score = sum(r['score'] for r in results) / total * 100
    
    report = f"""# M2 结果排序优化测试报告

**测试日期**: 2026-03-05  
**测试目标**: 评估结果排序和过滤效果

---

## 一、总体结果

| 指标 | 数值 |
|------|------|
| 总查询数 | {total} |
| 平均排序质量 | {avg_score:.1f}% |

**M2 目标**: ≥ 75%  
**当前状态**: {'✅ 达标' if avg_score >= 75 else '❌ 未达标'}

---

## 二、按类别统计

"""
    
    for category, stats in sorted(category_stats.items()):
        cat_score = stats['score_sum'] / stats['total'] * 100
        report += f"### {category}\n\n"
        report += f"- 查询数: {stats['total']}\n"
        report += f"- 平均排序质量: {cat_score:.1f}%\n\n"
    
    report += """---

## 三、优化建议

基于测试结果，建议：

1. 实现相关性评分算法
2. 添加结果去重逻辑
3. 优化时效性排序

---

**生成时间**: 2026-03-05  
**下一步**: 实施优化
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已生成: {report_path}")


if __name__ == "__main__":
    score = test_result_ranking()
    print(f"\n平均排序质量: {score:.1f}%")
    print(f"M2 目标: ≥ 75%")
    print(f"状态: {'✅ 达标' if score >= 75 else '❌ 未达标'}")
