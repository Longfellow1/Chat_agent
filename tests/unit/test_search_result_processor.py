"""
测试搜索结果处理模块
"""

import pytest
from agent_service.infra.tool_clients.search_result_processor import (
    calculate_relevance,
    dedup_results,
    score_credibility,
    process_search_results,
)


class TestCalculateRelevance:
    """测试相关性计算"""
    
    def test_perfect_match(self):
        """完全匹配应该得高分"""
        result = {
            "title": "Python 教程",
            "snippet": "学习 Python 编程的最佳教程"
        }
        keywords = ["Python", "教程"]
        score = calculate_relevance(result, keywords)
        assert score >= 0.8
    
    def test_partial_match(self):
        """部分匹配应该得中等分数"""
        result = {
            "title": "Python 编程",
            "snippet": "学习编程的基础知识"
        }
        keywords = ["Python", "教程"]
        score = calculate_relevance(result, keywords)
        assert 0.3 <= score < 0.8
    
    def test_no_match(self):
        """无匹配应该得低分"""
        result = {
            "title": "Java 开发",
            "snippet": "学习 Java 的基础知识"
        }
        keywords = ["Python", "教程"]
        score = calculate_relevance(result, keywords)
        assert score < 0.3
    
    def test_empty_keywords(self):
        """空关键词应该返回中等分数"""
        result = {
            "title": "Python 教程",
            "snippet": "学习 Python"
        }
        score = calculate_relevance(result, [])
        assert score == 0.5


class TestDedupResults:
    """测试去重"""
    
    def test_no_duplicates(self):
        """无重复时应该保持原样"""
        results = [
            {"title": "Python 教程", "url": "http://a.com"},
            {"title": "Java 教程", "url": "http://b.com"},
            {"title": "Go 教程", "url": "http://c.com"},
        ]
        deduped = dedup_results(results)
        assert len(deduped) == 3
    
    def test_exact_duplicates(self):
        """完全重复应该被去除"""
        results = [
            {"title": "Python 教程", "url": "http://a.com"},
            {"title": "Python 教程", "url": "http://b.com"},
            {"title": "Java 教程", "url": "http://c.com"},
        ]
        deduped = dedup_results(results)
        assert len(deduped) == 2
    
    def test_similar_titles(self):
        """相似标题应该被去除"""
        results = [
            {"title": "Python Programming Tutorial", "url": "http://a.com"},
            {"title": "Python Programming Tutorial Complete", "url": "http://b.com"},
            {"title": "Java Tutorial", "url": "http://c.com"},
        ]
        deduped = dedup_results(results, threshold=0.7)
        # 前两个标题相似度高，应该只保留一个
        assert len(deduped) <= 2
    
    def test_empty_results(self):
        """空结果应该返回空列表"""
        deduped = dedup_results([])
        assert deduped == []


class TestScoreCredibility:
    """测试可信度评分"""
    
    def test_gov_domain(self):
        """政府网站应该得最高分"""
        score = score_credibility("https://www.gov.cn/test")
        assert score == 10
    
    def test_edu_domain(self):
        """教育机构应该得高分"""
        score = score_credibility("https://www.tsinghua.edu.cn/test")
        assert score == 9
    
    def test_org_domain(self):
        """组织机构应该得较高分"""
        score = score_credibility("https://www.example.org.cn/test")
        assert score == 8
    
    def test_trusted_media(self):
        """知名媒体应该得高分"""
        score = score_credibility("https://www.xinhuanet.com/test")
        assert score == 10
        
        score = score_credibility("https://www.zhihu.com/test")
        assert score == 8
    
    def test_unknown_domain(self):
        """未知域名应该得中等分数"""
        score = score_credibility("https://www.unknown-site.com/test")
        assert score == 5
    
    def test_invalid_url(self):
        """无效 URL 应该得 0 分"""
        score = score_credibility("")
        assert score == 0
        
        score = score_credibility("not-a-url")
        assert score == 0


class TestProcessSearchResults:
    """测试完整的结果处理流程"""
    
    def test_full_pipeline(self):
        """测试完整流程：过滤 → 去重 → 评分 → 排序"""
        results = [
            {
                "title": "Python 教程 - 官方文档",
                "snippet": "学习 Python 编程的官方教程",
                "url": "https://www.python.org/doc"
            },
            {
                "title": "Python 教程 - 知乎",
                "snippet": "Python 编程入门教程",
                "url": "https://www.zhihu.com/python"
            },
            {
                "title": "Java 开发指南",
                "snippet": "学习 Java 的基础知识",
                "url": "https://www.example.com/java"
            },
            {
                "title": "Python 教程 - 知乎",  # 重复
                "snippet": "Python 编程入门教程",
                "url": "https://www.zhihu.com/python2"
            },
        ]
        
        processed = process_search_results(
            results,
            query="Python 教程",
            keywords=["Python", "教程"],
            max_results=3
        )
        
        # 应该过滤掉不相关的 Java 结果
        # 应该去重（两个知乎的 Python 教程）
        assert len(processed) <= 2
        
        # 每个结果应该有相关性、可信度和综合分数
        for result in processed:
            assert "relevance" in result
            assert "credibility" in result
            assert "score" in result
        
        # 结果应该按分数降序排列
        scores = [r["score"] for r in processed]
        assert scores == sorted(scores, reverse=True)
    
    def test_relevance_filtering(self):
        """测试相关性过滤"""
        results = [
            {
                "title": "Python 教程",
                "snippet": "学习 Python",
                "url": "http://a.com"
            },
            {
                "title": "完全不相关的内容",
                "snippet": "这是一个完全不相关的结果",
                "url": "http://b.com"
            },
        ]
        
        processed = process_search_results(
            results,
            query="Python 教程",
            keywords=["Python", "教程"],
            relevance_threshold=0.3
        )
        
        # 不相关的结果应该被过滤
        assert len(processed) == 1
        assert "Python" in processed[0]["title"]
    
    def test_max_results_limit(self):
        """测试最大结果数限制"""
        results = [
            {"title": f"Python 教程 {i}", "snippet": "学习 Python", "url": f"http://{i}.com"}
            for i in range(10)
        ]
        
        processed = process_search_results(
            results,
            query="Python 教程",
            max_results=3
        )
        
        assert len(processed) == 3
    
    def test_empty_results(self):
        """测试空结果"""
        processed = process_search_results(
            [],
            query="Python 教程",
            max_results=3
        )
        
        assert processed == []
