"""Unit tests for location intent parsing."""

from __future__ import annotations

import pytest

from agent_service.domain.location.intent import LocationIntent, AnchorType, SortBy
from agent_service.domain.location.parser import parse_location_intent
from agent_service.domain.location.dictionaries import (
    resolve_landmark,
    get_category_for_brand,
    parse_sort_intent,
    parse_constraints,
    parse_category,
    parse_brand,
)


class TestLocationIntent:
    """Test LocationIntent data model."""

    def test_location_intent_creation(self) -> None:
        """Test basic LocationIntent creation."""
        intent = LocationIntent(
            city="北京市",
            anchor_poi="鸟巢",
            brand="711",
            category="便利店",
        )
        
        assert intent.city == "北京市"
        assert intent.anchor_poi == "鸟巢"
        assert intent.brand == "711"
        assert intent.category == "便利店"

    def test_location_intent_is_complete(self) -> None:
        """Test is_complete method."""
        # Complete: city + anchor_poi
        intent1 = LocationIntent(city="北京市", anchor_poi="鸟巢")
        assert intent1.is_complete()
        
        # Complete: city + category
        intent2 = LocationIntent(city="北京市", category="便利店")
        assert intent2.is_complete()
        
        # Incomplete: no city
        intent3 = LocationIntent(anchor_poi="鸟巢")
        assert not intent3.is_complete()
        
        # Incomplete: city only
        intent4 = LocationIntent(city="北京市")
        assert not intent4.is_complete()

    def test_location_intent_to_dict(self) -> None:
        """Test to_dict method."""
        intent = LocationIntent(
            city="北京市",
            anchor_poi="鸟巢",
            sort_by=SortBy.DISTANCE,
            anchor_type=AnchorType.LANDMARK,
        )
        
        data = intent.to_dict()
        
        assert data["city"] == "北京市"
        assert data["anchor_poi"] == "鸟巢"
        assert data["sort_by"] == "distance"
        assert data["anchor_type"] == "landmark"

    def test_location_intent_to_tool_args(self) -> None:
        """Test to_tool_args method."""
        intent = LocationIntent(
            city="北京市",
            anchor_poi="鸟巢",
            brand="711",
        )
        
        args = intent.to_tool_args()
        
        assert args["city"] == "北京市"
        assert "鸟巢" in args["keyword"]
        assert "711" in args["keyword"]


class TestDictionaries:
    """Test dictionary functions."""

    def test_resolve_landmark(self) -> None:
        """Test landmark alias resolution."""
        assert resolve_landmark("鸟巢") == "国家体育场"
        assert resolve_landmark("水立方") == "国家游泳中心"
        assert resolve_landmark("世博源") == "上海世博会博物馆"
        assert resolve_landmark("unknown") == "unknown"

    def test_get_category_for_brand(self) -> None:
        """Test brand to category mapping."""
        assert get_category_for_brand("711") == "便利店"
        assert get_category_for_brand("全家") == "便利店"
        assert get_category_for_brand("肯德基") == "快餐"
        assert get_category_for_brand("星巴克") == "咖啡厅"
        assert get_category_for_brand("unknown") == ""

    def test_parse_sort_intent(self) -> None:
        """Test sort intent parsing."""
        sort_by, order = parse_sort_intent("最近的711")
        assert sort_by == "distance"
        assert order == "asc"
        
        sort_by, order = parse_sort_intent("最好评的餐厅")
        assert sort_by == "rating"
        assert order == "desc"
        
        sort_by, order = parse_sort_intent("人均最低的火锅")
        assert sort_by == "price"
        assert order == "asc"
        
        sort_by, order = parse_sort_intent("随便找个餐厅")
        assert sort_by == "distance"
        assert order == "asc"

    def test_parse_constraints(self) -> None:
        """Test constraint parsing."""
        constraints = parse_constraints("24小时便利店")
        assert constraints.get("open_24h") is True
        
        constraints = parse_constraints("有停车位的餐厅")
        assert constraints.get("has_parking") is True
        
        constraints = parse_constraints("有wifi的咖啡厅")
        assert constraints.get("has_wifi") is True
        
        constraints = parse_constraints("普通餐厅")
        assert len(constraints) == 0

    def test_parse_category(self) -> None:
        """Test category parsing."""
        assert parse_category("附近的餐厅") == "餐厅"
        assert parse_category("周边的便利店") == "便利店"
        assert parse_category("最近的医院") == "医院"
        assert parse_category("附近的酒店") == "酒店"
        assert parse_category("随便") == ""

    def test_parse_brand(self) -> None:
        """Test brand parsing."""
        assert parse_brand("最近的711") == "711"
        assert parse_brand("附近的肯德基") == "肯德基"
        assert parse_brand("星巴克咖啡") == "星巴克"
        assert parse_brand("随便找个餐厅") == ""


class TestParseLocationIntent:
    """Test location intent parser."""

    def test_parse_simple_nearby_query(self) -> None:
        """Test parsing simple nearby query."""
        query = "北京市附近的餐厅"
        intent = parse_location_intent(query)
        
        assert intent.city == "北京市"
        assert intent.category == "餐厅"
        assert intent.is_complete()

    def test_parse_anchor_and_brand_query(self) -> None:
        """Test parsing query with anchor and brand."""
        query = "北京市的鸟巢周边，最近的711是哪一家"
        intent = parse_location_intent(query)
        
        assert intent.city == "北京市"
        assert intent.anchor_poi == "国家体育场"  # Resolved from 鸟巢
        assert intent.brand == "711"
        assert intent.category == "便利店"  # Inferred from brand
        assert intent.sort_by == SortBy.DISTANCE
        assert intent.is_complete()

    def test_parse_with_sort_intent(self) -> None:
        """Test parsing with sort intent."""
        query = "北京市最好评的餐厅"
        intent = parse_location_intent(query)
        
        assert intent.city == "北京市"
        assert intent.category == "餐厅"
        assert intent.sort_by == SortBy.RATING
        assert intent.sort_order == "desc"

    def test_parse_with_constraints(self) -> None:
        """Test parsing with constraints."""
        query = "北京市24小时便利店"
        intent = parse_location_intent(query)
        
        assert intent.city == "北京市"
        assert intent.category == "便利店"
        assert intent.constraints.get("open_24h") is True

    def test_parse_incomplete_query(self) -> None:
        """Test parsing incomplete query."""
        query = "附近的餐厅"
        intent = parse_location_intent(query)
        
        assert intent.city == ""
        assert intent.category == "餐厅"
        assert not intent.is_complete()

    def test_parse_complex_query(self) -> None:
        """Test parsing complex query."""
        query = "上海市陆家嘴周边，最好评的火锅，要有停车位"
        intent = parse_location_intent(query)
        
        assert intent.city == "上海市"
        # Note: 陆家嘴 is recognized as anchor_poi (landmark), not district
        assert intent.anchor_poi == "陆家嘴金融区"
        assert intent.category == "火锅"
        assert intent.sort_by == SortBy.RATING
        assert intent.sort_order == "desc"
        assert intent.constraints.get("has_parking") is True

    def test_parse_confidence_calculation(self) -> None:
        """Test confidence score calculation."""
        # Low confidence: only category
        intent1 = parse_location_intent("附近的餐厅")
        assert intent1.confidence < 0.5
        
        # High confidence: city + anchor + brand + sort
        intent2 = parse_location_intent("北京市的鸟巢周边最近的711")
        assert intent2.confidence > 0.7

    def test_parse_multiple_cities(self) -> None:
        """Test parsing with multiple city mentions."""
        query = "北京市和上海市的餐厅"
        intent = parse_location_intent(query)
        
        # Should extract first city
        assert intent.city in ("北京市", "上海市")

    def test_parse_with_district(self) -> None:
        """Test parsing with district."""
        query = "北京市朝阳区的餐厅"
        intent = parse_location_intent(query)
        
        assert intent.city == "北京市"
        assert intent.district == "朝阳区"
        assert intent.category == "餐厅"

    def test_parse_brand_infers_category(self) -> None:
        """Test that brand parsing infers category."""
        query = "北京市附近的711"
        intent = parse_location_intent(query)
        
        assert intent.brand == "711"
        assert intent.category == "便利店"  # Inferred from brand

    def test_parse_to_tool_args(self) -> None:
        """Test conversion to tool arguments."""
        query = "北京市的鸟巢周边最近的711"
        intent = parse_location_intent(query)
        
        args = intent.to_tool_args()
        
        assert args["city"] == "北京市"
        assert "鸟巢" in args["keyword"] or "国家体育场" in args["keyword"]
        assert "711" in args["keyword"]


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_query(self) -> None:
        """Test parsing empty query."""
        intent = parse_location_intent("")
        
        assert intent.city == ""
        assert intent.category == ""
        assert not intent.is_complete()

    def test_query_with_only_city(self) -> None:
        """Test query with only city."""
        intent = parse_location_intent("北京市")
        
        assert intent.city == "北京市"
        assert not intent.is_complete()

    def test_query_with_special_characters(self) -> None:
        """Test query with special characters."""
        query = "北京市@鸟巢#周边$最近的711"
        intent = parse_location_intent(query)
        
        # Should still extract key information
        assert intent.city == "北京市"

    def test_query_with_numbers(self) -> None:
        """Test query with numbers."""
        query = "北京市2号线附近的餐厅"
        intent = parse_location_intent(query)
        
        assert intent.city == "北京市"
        assert intent.category == "餐厅"

    def test_case_insensitive_brand_matching(self) -> None:
        """Test case-insensitive brand matching."""
        query = "北京市附近的KFC"
        intent = parse_location_intent(query)
        
        assert intent.brand == "肯德基"  # Should match KFC
        assert intent.category == "快餐"
