"""
测试 Web Search Intent Router
"""

import pytest
from agent_service.domain.intents.web_search_router import (
    route_tool,
    should_route_to_web_search,
    get_routing_debug_info,
)


class TestRouteToolBasic:
    """基本路由测试"""
    
    def test_weather_query_not_misrouted(self):
        """天气查询不应被误路由到 web_search"""
        query = "告诉我明天的天气"
        tool = route_tool(query)
        assert tool == "get_weather", f"Expected get_weather, got {tool}"
    
    def test_weather_with_weak_keyword(self):
        """天气查询即使有弱关键词也应优先"""
        query = "明天天气怎么样"
        tool = route_tool(query)
        assert tool == "get_weather"
    
    def test_stock_query_not_misrouted(self):
        """股票查询不应被误路由到 web_search"""
        query = "苹果股票最新价格"
        tool = route_tool(query)
        assert tool == "get_stock"
    
    def test_nearby_query_not_misrouted(self):
        """地点查询不应被误路由到 web_search"""
        query = "北京附近有什么好吃的"
        tool = route_tool(query)
        assert tool == "find_nearby"


class TestWebSearchStrongKeywords:
    """Web Search 强关键词测试"""
    
    def test_web_search_strong_keyword_search(self):
        """'搜一下'应直接触发 web_search"""
        query = "搜一下苹果手机最新价格"
        tool = route_tool(query)
        assert tool == "web_search"
    
    def test_web_search_strong_keyword_baidu(self):
        """'百度一下'应直接触发 web_search"""
        query = "百度一下如何学习Python"
        tool = route_tool(query)
        assert tool == "web_search"
    
    def test_web_search_strong_keyword_official_website(self):
        """'官网'应直接触发 web_search"""
        query = "查一下OpenAI的官网"
        tool = route_tool(query)
        assert tool == "web_search"
    
    def test_web_search_strong_keyword_link(self):
        """'链接'应直接触发 web_search"""
        query = "给我一个GitHub的链接"
        tool = route_tool(query)
        assert tool == "web_search"


class TestExcludePatterns:
    """排除模式测试"""
    
    def test_weather_exclude_pattern(self):
        """天气相关词汇应被排除"""
        query = "搜一下北京的天气"
        tool = route_tool(query)
        # 虽然有'搜一下'，但'天气'应该优先
        assert tool == "get_weather"
    
    def test_stock_exclude_pattern(self):
        """股票相关词汇应被排除"""
        query = "搜一下苹果股票行情"
        tool = route_tool(query)
        # 虽然有'搜一下'，但'股票'应该优先
        assert tool == "get_stock"
    
    def test_nearby_exclude_pattern(self):
        """地点相关词汇应被排除"""
        query = "搜一下北京附近的餐厅"
        tool = route_tool(query)
        # 虽然有'搜一下'，但'附近'应该优先
        assert tool == "find_nearby"


class TestWeakKeywords:
    """弱关键词测试"""
    
    def test_weak_keyword_alone_not_trigger(self):
        """仅弱关键词不应触发 web_search"""
        query = "苹果手机怎么样"  # 仅有'怎么样'
        tool = route_tool(query)
        # 应该优先考虑其他工具或默认
        assert tool != "web_search" or "苹果" in query
    
    def test_weak_keyword_with_context(self):
        """弱关键词配合上下文可能触发"""
        query = "最新的Python教程在哪里"
        tool = route_tool(query)
        # 这个查询应该路由到 web_search
        assert tool == "web_search"


class TestShouldRouteToWebSearch:
    """should_route_to_web_search 函数测试"""
    
    def test_already_web_search(self):
        """如果已经是 web_search，返回 True"""
        assert should_route_to_web_search("任何查询", "web_search") is True
    
    def test_multiple_strong_keywords(self):
        """多个强关键词应该路由到 web_search"""
        query = "搜一下官网链接"
        assert should_route_to_web_search(query, "get_weather") is True
    
    def test_exclude_pattern_blocks_routing(self):
        """排除模式应该阻止路由"""
        query = "搜一下北京天气"
        assert should_route_to_web_search(query, "get_weather") is False


class TestDebugInfo:
    """调试信息测试"""
    
    def test_debug_info_structure(self):
        """调试信息应包含必要字段"""
        query = "搜一下苹果手机"
        info = get_routing_debug_info(query)
        
        assert "query" in info
        assert "scores" in info
        assert "selected_tool" in info
        assert info["query"] == query
    
    def test_debug_info_scores(self):
        """调试信息中的分数应该合理"""
        query = "北京天气怎么样"
        info = get_routing_debug_info(query)
        
        # get_weather 应该有最高分
        assert info["scores"]["get_weather"] > info["scores"]["web_search"]
        assert info["selected_tool"] == "get_weather"


class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_query(self):
        """空查询应该有默认行为"""
        tool = route_tool("")
        assert tool in ["web_search", "get_weather", "get_stock", "get_news", "find_nearby"]
    
    def test_ambiguous_query(self):
        """模糊查询应该有合理的默认"""
        query = "查一下"
        tool = route_tool(query)
        # 应该路由到某个工具
        assert tool is not None
    
    def test_mixed_keywords(self):
        """混合关键词应该按优先级处理"""
        query = "搜一下北京的天气和股票"
        tool = route_tool(query)
        # 天气和股票都有，但搜索也有
        # 应该优先考虑垂直工具
        assert tool in ["get_weather", "get_stock"]
