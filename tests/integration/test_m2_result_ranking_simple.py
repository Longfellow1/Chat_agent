"""
M2 任务3：结果排序优化测试（简化版）

直接测试排序算法是否正确工作
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from infra.tool_clients.search_result_processor import SearchResultProcessor


def test_ranking_algorithm():
    """测试排序算法"""
    print("=" * 80)
    print("M2 任务3：结果排序算法测试")
    print("=" * 80)
    print()
    
    processor = SearchResultProcessor(max_results=5, relevance_threshold=0.0, dedup_threshold=0.5)  # 降低去重阈值
    
    # 测试用例1：时效性排序
    print("测试1：时效性排序")
    results1 = [
        {
            "title": "旧文章",
            "url": "https://example.com/old",
            "content": "旧内容",
            "published_date": "2024-01-01",
        },
        {
            "title": "新文章",
            "url": "https://example.com/new",
            "content": "新内容",
            "published_date": "2026-03-05",
        },
    ]
    
    ranked1 = processor.process_results(results1, "测试查询")
    print(f"  输入: 旧文章(2024) vs 新文章(2026)")
    print(f"  排序后第1名: {ranked1[0]['title']} ({ranked1[0]['published_date']})")
    print(f"  ✅ 通过" if ranked1[0]['title'] == "新文章" else "  ❌ 失败")
    print()
    
    # 测试用例2：可信度排序
    print("测试2：可信度排序")
    results2 = [
        {
            "title": "个人博客",
            "url": "https://blog.example.com",
            "content": "个人观点",
            "published_date": "2026-03-05",
        },
        {
            "title": "官方媒体",
            "url": "https://xinhuanet.com",
            "content": "官方报道",
            "published_date": "2026-03-05",
        },
    ]
    
    ranked2 = processor.process_results(results2, "测试查询")
    print(f"  输入: 个人博客 vs 官方媒体(xinhuanet)")
    print(f"  排序后第1名: {ranked2[0]['title']}")
    print(f"  ✅ 通过" if ranked2[0]['title'] == "官方媒体" else "  ❌ 失败")
    print()
    
    # 测试用例3：相关性排序
    print("测试3：相关性排序")
    results3 = [
        {
            "title": "不相关文章",
            "url": "https://example.com",
            "content": "完全不相关的内容",
            "published_date": "2026-03-05",
        },
        {
            "title": "Python教程 - 如何学习Python",
            "url": "https://example.com",
            "content": "Python是一门编程语言，学习Python需要...",
            "published_date": "2026-03-05",
        },
    ]
    
    ranked3 = processor.process_results(results3, "Python教程")
    print(f"  输入: 不相关文章 vs Python教程")
    print(f"  排序后第1名: {ranked3[0]['title']}")
    print(f"  ✅ 通过" if "Python" in ranked3[0]['title'] else "  ❌ 失败")
    print()
    
    # 测试用例4：去重
    print("测试4：去重")
    results4 = [
        {
            "title": "iPhone 15 价格",
            "url": "https://example1.com",
            "content": "iPhone 15 售价...",
            "published_date": "2026-03-05",
        },
        {
            "title": "iPhone 15 的价格",
            "url": "https://example2.com",
            "content": "iPhone 15 价格是...",
            "published_date": "2026-03-05",
        },
        {
            "title": "华为 Mate 60 价格",
            "url": "https://example3.com",
            "content": "华为 Mate 60 售价...",
            "published_date": "2026-03-05",
        },
    ]
    
    ranked4 = processor.process_results(results4, "手机价格")
    print(f"  输入: 3篇文章（2篇相似）")
    print(f"  去重后数量: {len(ranked4)}")
    print(f"  ✅ 通过" if len(ranked4) == 2 else "  ❌ 失败")
    print()
    
    # 测试用例5：综合排序
    print("测试5：综合排序（相关性 + 可信度 + 时效性）")
    results5 = [
        {
            "title": "Python教程",
            "url": "https://blog.example.com",  # 低可信度
            "content": "Python是...",
            "published_date": "2024-01-01",  # 旧
        },
        {
            "title": "Python教程",
            "url": "https://edu.cn",  # 高可信度
            "content": "Python是...",
            "published_date": "2026-03-05",  # 新
        },
        {
            "title": "不相关",
            "url": "https://gov.cn",  # 高可信度
            "content": "完全不相关",
            "published_date": "2026-03-05",  # 新
        },
    ]
    
    ranked5 = processor.process_results(results5, "Python教程")
    print(f"  输入: 旧博客 vs 新edu vs 不相关gov")
    print(f"  排序后第1名: {ranked5[0]['title']} ({ranked5[0]['url']})")
    print(f"  ✅ 通过" if "edu.cn" in ranked5[0]['url'] else "  ❌ 失败")
    print()
    
    print("=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_ranking_algorithm()
