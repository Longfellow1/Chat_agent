"""Unit tests for encyclopedia router."""

import sys
from pathlib import Path

import pytest

# Add agent_service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from domain.intents.encyclopedia_router import EncyclopediaRouter


class TestEncyclopediaRouter:
    """Test encyclopedia router."""
    
    def test_encyclopedia_keywords(self):
        """Test queries with encyclopedia keywords."""
        router = EncyclopediaRouter()
        
        encyclopedia_queries = [
            "什么是电动汽车",
            "电动汽车是什么",
            "特斯拉公司介绍",
            "锂电池原理",
            "新能源汽车发展历史",
            "马斯克是谁",
            "谁是马斯克",
            "电动汽车概念",
            "充电桩定义",
        ]
        
        for query in encyclopedia_queries:
            result = router.route(query)
            assert result == "encyclopedia", f"Failed for query: {query}"
    
    def test_web_search_keywords(self):
        """Test queries with web search keywords."""
        router = EncyclopediaRouter()
        
        web_search_queries = [
            "特斯拉 Model 3 价格",
            "电动车多少钱",
            "比亚迪和特斯拉哪个好",
            "电动车怎么样",
            "如何选择电动车",
            "蔚来最新消息",
            "电动车充电攻略",
            "上海电动车补贴政策",
            "特斯拉评测",
        ]
        
        for query in web_search_queries:
            result = router.route(query)
            assert result == "web_search", f"Failed for query: {query}"
    
    def test_short_queries(self):
        """Test short queries without explicit keywords."""
        router = EncyclopediaRouter()
        
        # Short queries without search keywords -> encyclopedia
        assert router.route("特斯拉") == "encyclopedia"
        assert router.route("电动车") == "encyclopedia"
        
        # Short queries with search keywords -> web_search
        assert router.route("特斯拉价格") == "web_search"
        assert router.route("电动车多少钱") == "web_search"
    
    def test_should_use_encyclopedia(self):
        """Test should_use_encyclopedia method."""
        router = EncyclopediaRouter()
        
        # Encyclopedia queries
        assert router.should_use_encyclopedia("什么是电动汽车")
        assert router.should_use_encyclopedia("特斯拉介绍")
        assert router.should_use_encyclopedia("锂电池原理")
        assert router.should_use_encyclopedia("特斯拉")  # Short query
        
        # Web search queries
        assert not router.should_use_encyclopedia("特斯拉价格")
        assert not router.should_use_encyclopedia("比亚迪怎么样")
        assert not router.should_use_encyclopedia("电动车最新消息")
    
    def test_case_insensitive(self):
        """Test case insensitive matching."""
        router = EncyclopediaRouter()
        
        # Same query, different cases
        assert router.route("什么是电动汽车") == "encyclopedia"
        assert router.route("什么是电动汽车") == "encyclopedia"
        
        assert router.route("特斯拉价格") == "web_search"
        assert router.route("特斯拉价格") == "web_search"
