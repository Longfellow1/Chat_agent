"""Integration tests for location intent with tool execution."""

from __future__ import annotations

import pytest

from agent_service.domain.location.intent import LocationIntent, SortBy
from agent_service.domain.location.parser import parse_location_intent
from agent_service.domain.tools.planner_v2 import build_tool_plan_v2, extract_location_intent
from agent_service.infra.tool_clients.mcp_gateway import MCPToolGateway


class TestLocationIntentIntegration:
    """Test location intent integration with tools."""

    def test_build_tool_plan_v2_find_nearby(self) -> None:
        """Test building tool plan for find_nearby."""
        query = "北京市的鸟巢周边最近的711"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        assert plan["tool_name"] == "find_nearby"
        assert "keyword" in plan["tool_args"]
        assert "city" in plan["tool_args"]
        assert plan["tool_args"]["city"] == "北京市"
        assert len(plan["missing_slots"]) == 0
        assert plan["confidence"] > 0.7

    def test_build_tool_plan_v2_incomplete_intent(self) -> None:
        """Test building tool plan with incomplete intent."""
        query = "附近的餐厅"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        assert plan["tool_name"] == "find_nearby"
        assert "city" in plan["missing_slots"]
        assert plan["error"] == "incomplete_intent"

    def test_build_tool_plan_v2_other_tools(self) -> None:
        """Test building tool plan for other tools."""
        query = "北京明天天气怎么样"
        plan = build_tool_plan_v2(query, "get_weather", use_location_intent=False)
        
        assert plan["tool_name"] == "get_weather"
        assert "city" in plan["tool_args"]

    def test_extract_location_intent_convenience(self) -> None:
        """Test convenience function for location intent extraction."""
        query = "北京市的鸟巢周边最近的711"
        intent = extract_location_intent(query)
        
        assert isinstance(intent, LocationIntent)
        assert intent.city == "北京市"
        assert intent.brand == "711"

    def test_mcp_gateway_invoke_with_intent(self) -> None:
        """Test MCPToolGateway invoke_with_intent method."""
        gateway = MCPToolGateway()
        query = "北京市的鸟巢周边最近的711"
        
        result, intent = gateway.invoke_with_intent("find_nearby", query)
        
        assert isinstance(intent, LocationIntent)
        assert intent.city == "北京市"
        assert intent.brand == "711"
        assert result.raw is not None
        assert "intent" in result.raw

    def test_mcp_gateway_invoke_nearby_with_intent(self) -> None:
        """Test MCPToolGateway invoke_nearby_with_intent method."""
        gateway = MCPToolGateway()
        query = "鸟巢周边最近的711"
        
        result, intent = gateway.invoke_nearby_with_intent(query, city="北京市")
        
        assert isinstance(intent, LocationIntent)
        assert intent.city == "北京市"
        assert intent.anchor_poi == "国家体育场"  # Resolved from 鸟巢
        assert intent.brand == "711"

    def test_location_intent_with_sort_by(self) -> None:
        """Test location intent with sort_by."""
        query = "北京市最好评的餐厅"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        intent = LocationIntent(**plan["intent"])
        assert intent.sort_by == SortBy.RATING
        assert intent.sort_order == "desc"

    def test_location_intent_with_constraints(self) -> None:
        """Test location intent with constraints."""
        query = "北京市24小时便利店"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        intent = LocationIntent(**plan["intent"])
        assert intent.constraints.get("open_24h") is True

    def test_location_intent_to_tool_args_format(self) -> None:
        """Test location intent conversion to tool args format."""
        query = "北京市的鸟巢周边最近的711"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        tool_args = plan["tool_args"]
        
        # Should have keyword and city
        assert "keyword" in tool_args
        assert "city" in tool_args
        
        # Keyword should contain anchor and brand
        keyword = tool_args["keyword"]
        assert "鸟巢" in keyword or "国家体育场" in keyword
        assert "711" in keyword

    def test_location_intent_confidence_score(self) -> None:
        """Test confidence score calculation."""
        # Low confidence: only category
        plan1 = build_tool_plan_v2("附近的餐厅", "find_nearby", use_location_intent=True)
        confidence1 = plan1.get("confidence", 0)
        
        # High confidence: city + anchor + brand
        plan2 = build_tool_plan_v2(
            "北京市的鸟巢周边最近的711",
            "find_nearby",
            use_location_intent=True,
        )
        confidence2 = plan2.get("confidence", 0)
        
        assert confidence2 > confidence1

    def test_location_intent_with_district(self) -> None:
        """Test location intent with district."""
        query = "北京市朝阳区的餐厅"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        intent = LocationIntent(**plan["intent"])
        assert intent.city == "北京市"
        assert intent.district == "朝阳区"

    def test_location_intent_brand_infers_category(self) -> None:
        """Test that brand parsing infers category."""
        query = "北京市附近的711"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        intent = LocationIntent(**plan["intent"])
        assert intent.brand == "711"
        assert intent.category == "便利店"

    def test_location_intent_multiple_keywords(self) -> None:
        """Test location intent with multiple keywords."""
        query = "北京市的鸟巢周边，最近的711或全家便利店"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        intent = LocationIntent(**plan["intent"])
        assert intent.city == "北京市"
        # Should extract at least one brand
        assert intent.brand in ("711", "全家")


class TestLocationIntentEdgeCases:
    """Test edge cases in location intent integration."""

    def test_empty_query(self) -> None:
        """Test with empty query."""
        plan = build_tool_plan_v2("", "find_nearby", use_location_intent=True)
        
        assert "error" in plan or len(plan["missing_slots"]) > 0

    def test_query_with_only_city(self) -> None:
        """Test query with only city."""
        plan = build_tool_plan_v2("北京市", "find_nearby", use_location_intent=True)
        
        assert "city" in plan["missing_slots"]

    def test_query_with_special_characters(self) -> None:
        """Test query with special characters."""
        query = "北京市@鸟巢#周边$最近的711"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
        
        # Should still extract key information
        intent = LocationIntent(**plan["intent"])
        assert intent.city == "北京市"

    def test_fallback_to_existing_planner(self) -> None:
        """Test fallback to existing planner for non-location tools."""
        query = "北京明天天气怎么样"
        plan = build_tool_plan_v2(query, "get_weather", use_location_intent=False)
        
        assert plan["tool_name"] == "get_weather"
        assert "city" in plan["tool_args"]

    def test_location_intent_disable_flag(self) -> None:
        """Test disabling location intent parsing."""
        query = "北京市的鸟巢周边最近的711"
        plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=False)
        
        # Should use existing planner logic
        assert plan["tool_name"] == "find_nearby"
        # May not have full intent parsing
        assert "intent" not in plan or plan.get("intent") is None
