"""
Test: 4B Router with Logprobs Validation

测试规则 + LLM 兜底的效果
"""

import pytest
import json
from agent_service.domain.intents.router_4b_with_logprobs import (
    Router4BWithLogprobs,
    RuleBasedRouter,
    LogprobsValidator,
    ToolType,
)


class TestRuleBasedRouter:
    """测试规则路由器"""
    
    def test_plan_trip_with_destination_and_time(self):
        """测试：目的地 + 时间 = plan_trip"""
        result = RuleBasedRouter.try_route("我想去北京3天")
        
        assert result is not None
        assert result.tool == ToolType.PLAN_TRIP
        assert result.params["destination"] == "北京"
        assert result.confidence > 0.8
    
    def test_find_nearby_with_location_and_category(self):
        """测试：位置 + 类别 = find_nearby"""
        result = RuleBasedRouter.try_route("北京附近有什么好吃的")
        
        assert result is not None
        assert result.tool == ToolType.FIND_NEARBY
        assert result.params["city"] == "北京"
        assert result.params["category"] == "餐厅"
        assert result.confidence > 0.8
    
    def test_get_weather_with_location(self):
        """测试：天气关键词 + 位置 = get_weather"""
        result = RuleBasedRouter.try_route("北京的天气怎么样")
        
        assert result is not None
        assert result.tool == ToolType.GET_WEATHER
        assert result.params["location"] == "北京"
    
    def test_rule_cannot_handle_ambiguous_query(self):
        """测试：规则无法处理模糊查询"""
        result = RuleBasedRouter.try_route("什么是人工智能")
        
        # 规则无法处理，返回 None
        assert result is None
    
    def test_rule_cannot_handle_incomplete_params(self):
        """测试：规则无法处理参数不完整的查询"""
        result = RuleBasedRouter.try_route("我想去北京")  # 缺少时间
        
        # 规则无法处理，返回 None
        assert result is None


class TestLogprobsValidator:
    """测试 Logprobs 验证器"""
    
    def test_well_formed_json_high_confidence(self):
        """测试：完整 JSON = 高置信度"""
        response = '{"tool": "plan_trip", "params": {"destination": "北京"}}'
        confidence = LogprobsValidator.extract_confidence(response)
        
        assert confidence > 0.8
    
    def test_malformed_json_low_confidence(self):
        """测试：格式错误 = 低置信度"""
        response = '{"tool": "plan_trip", "params": {"destination"'
        confidence = LogprobsValidator.extract_confidence(response)
        
        assert confidence < 0.5
    
    def test_fallback_threshold(self):
        """测试：置信度阈值"""
        # 高于阈值：不触发澄清
        assert not LogprobsValidator.should_fallback(0.8, threshold=0.7)
        
        # 低于阈值：触发澄清
        assert LogprobsValidator.should_fallback(0.6, threshold=0.7)


class TestRouter4BWithLogprobs:
    """测试 4B Router"""
    
    def test_rule_handles_simple_query(self):
        """测试：规则处理简单查询"""
        router = Router4BWithLogprobs()
        
        result = router.route("我想去北京3天")
        
        assert result["success"] is True
        assert result["tool"] == "plan_trip"
        assert result["source"] == "rule"
        assert result["confidence"] > 0.8
    
    def test_llm_fallback_for_complex_query(self):
        """测试：LLM 兜底处理复杂查询"""
        router = Router4BWithLogprobs()
        
        # 没有 LLM 客户端，应该返回失败
        result = router.route("什么是人工智能")
        
        assert result["success"] is False
        assert result["source"] == "none"
    
    def test_result_structure(self):
        """测试：结果结构"""
        router = Router4BWithLogprobs()
        
        result = router.route("我想去北京3天")
        
        # 检查必需字段
        assert "success" in result
        assert "tool" in result
        assert "params" in result
        assert "confidence" in result
        assert "needs_clarification" in result
        assert "source" in result
        
        # 检查类型
        assert isinstance(result["success"], bool)
        assert isinstance(result["tool"], str)
        assert isinstance(result["params"], dict)
        assert isinstance(result["confidence"], float)
        assert isinstance(result["needs_clarification"], bool)
        assert isinstance(result["source"], str)


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_query(self):
        """测试：空查询"""
        router = Router4BWithLogprobs()
        result = router.route("")
        
        # 不应该崩溃
        assert "tool" in result
        assert "params" in result
    
    def test_very_long_query(self):
        """测试：很长的查询"""
        router = Router4BWithLogprobs()
        long_query = "我想去北京" * 100
        result = router.route(long_query)
        
        # 不应该崩溃
        assert "tool" in result
        assert "params" in result
    
    def test_special_characters(self):
        """测试：特殊字符"""
        router = Router4BWithLogprobs()
        query = "我想去北京@#$%^&*()"
        result = router.route(query)
        
        # 不应该崩溃
        assert "tool" in result
        assert "params" in result


class TestSystemPrompt:
    """测试系统提示词"""
    
    def test_system_prompt_is_optimized_for_4b(self):
        """测试：提示词针对 4B 优化"""
        router = Router4BWithLogprobs()
        prompt = router.SYSTEM_PROMPT
        
        # 应该包含关键元素
        assert "plan_trip" in prompt
        assert "find_nearby" in prompt
        assert "web_search" in prompt
        
        # 不应该包含 reasoning
        assert "reasoning" not in prompt.lower() or "无 reasoning" in prompt
        
        # 应该包含极简 JSON 示例
        assert "极简 JSON" in prompt or "JSON" in prompt


class TestIntegration:
    """集成测试"""
    
    def test_rule_then_llm_fallback_flow(self):
        """测试：规则 → LLM 兜底流程"""
        router = Router4BWithLogprobs()
        
        # 简单查询：规则处理
        simple_result = router.route("我想去北京3天")
        assert simple_result["source"] == "rule"
        
        # 复杂查询：LLM 兜底（但没有 LLM 客户端）
        complex_result = router.route("什么是人工智能")
        assert complex_result["source"] == "none"  # 因为没有 LLM 客户端
    
    def test_multiple_queries(self):
        """测试：多个查询"""
        router = Router4BWithLogprobs()
        
        queries = [
            ("我想去北京3天", "plan_trip"),
            ("北京附近有什么好吃的", "find_nearby"),
            ("北京的天气怎么样", "get_weather"),
        ]
        
        for query, expected_tool in queries:
            result = router.route(query)
            assert result["tool"] == expected_tool


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
