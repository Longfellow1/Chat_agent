"""
测试 planner.py 中的 web_search 查询优化
"""

import pytest
from agent_service.domain.tools.planner import (
    extract_rule_tool_args,
    build_tool_plan,
    _identify_entity_type,
)


class TestWebSearchQueryOptimization:
    """测试 web_search 查询优化"""
    
    def test_time_normalization(self):
        """测试时间标准化"""
        result = extract_rule_tool_args("3月15日的天气预报", "web_search")
        # 应该包含当前年份
        assert "query" in result
        from datetime import datetime
        current_year = datetime.now().year
        assert str(current_year) in result["query"]
    
    def test_stopword_removal(self):
        """测试停用词去除"""
        result = extract_rule_tool_args("帮我查一下Python教程", "web_search")
        # 停用词应该被去除或标准化
        assert "query" in result
        # 查询应该被优化
        assert result["query"] != "帮我查一下Python教程"
    
    def test_entity_type_person(self):
        """测试人物实体识别"""
        result = extract_rule_tool_args("谁是马斯克", "web_search")
        assert result.get("entity_type") == "person"
    
    def test_entity_type_concept(self):
        """测试概念实体识别"""
        result = extract_rule_tool_args("什么是人工智能", "web_search")
        assert result.get("entity_type") == "concept"
    
    def test_entity_type_product(self):
        """测试产品实体识别"""
        result = extract_rule_tool_args("iPhone 15 价格", "web_search")
        assert result.get("entity_type") == "product"
    
    def test_entity_type_event(self):
        """测试事件实体识别"""
        result = extract_rule_tool_args("奥运会什么时候举办", "web_search")
        assert result.get("entity_type") == "event"
    
    def test_no_entity_type(self):
        """测试无明确实体类型"""
        result = extract_rule_tool_args("Python 教程", "web_search")
        # 可能没有 entity_type 或为 None
        assert result.get("entity_type") is None or "entity_type" not in result


class TestBuildToolPlan:
    """测试 build_tool_plan"""
    
    def test_web_search_plan(self):
        """测试 web_search 工具计划"""
        plan = build_tool_plan("搜一下Python教程", "web_search")
        
        assert plan.tool_name == "web_search"
        assert "query" in plan.tool_args
        assert plan.missing_slots == []
    
    def test_web_search_with_entity_type(self):
        """测试带实体类型的工具计划"""
        plan = build_tool_plan("谁是马斯克", "web_search")
        
        assert plan.tool_name == "web_search"
        assert "query" in plan.tool_args
        assert plan.tool_args.get("entity_type") == "person"


class TestIdentifyEntityType:
    """测试实体类型识别"""
    
    def test_person_keywords(self):
        """测试人物关键词"""
        assert _identify_entity_type("谁是马斯克") == "person"
        assert _identify_entity_type("这个演员是什么人") == "person"
        assert _identify_entity_type("周杰伦是明星吗") == "person"
    
    def test_concept_keywords(self):
        """测试概念关键词"""
        assert _identify_entity_type("什么是人工智能") == "concept"
        assert _identify_entity_type("区块链是什么") == "concept"
        assert _identify_entity_type("解释一下量子计算") == "concept"
    
    def test_product_keywords(self):
        """测试产品关键词"""
        assert _identify_entity_type("iPhone 15 价格") == "product"
        assert _identify_entity_type("这个手机多少钱") == "product"
        assert _identify_entity_type("怎么购买") == "product"
    
    def test_event_keywords(self):
        """测试事件关键词"""
        assert _identify_entity_type("奥运会什么时候举办") == "event"
        assert _identify_entity_type("发布会几点开始") == "event"
        assert _identify_entity_type("这个事件发生在什么时间") == "event"
    
    def test_no_entity_type(self):
        """测试无明确实体类型"""
        assert _identify_entity_type("Python 教程") is None
        assert _identify_entity_type("如何学习编程") is None
