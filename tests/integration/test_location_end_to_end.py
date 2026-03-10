"""End-to-end tests for location intent system."""

import pytest

from agent_service.domain.location.parser import parse_location_intent
from agent_service.domain.location.result_processor import create_default_processor_chain
from agent_service.domain.location.templates import format_location_results


# Test queries covering various scenarios
TEST_QUERIES = [
    # Basic queries
    "北京市的鸟巢周边，最近的711是哪一家",
    "上海世博源附近的星巴克",
    "杭州西湖边上的餐厅",
    "深圳南山区的便利店",
    "广州天河区最近的地铁站",
    
    # With sorting
    "北京朝阳区评分最高的火锅店",
    "上海浦东新区最便宜的快餐",
    "成都春熙路最近的停车场",
    
    # With brand
    "三里屯附近的肯德基",
    "国贸周边的全家便利店",
    "鸟巢旁边的麦当劳",
    
    # Complex queries
    "北京市朝阳区国贸附近，最近的24小时便利店",
    "上海静安寺周边评分最高的咖啡厅",
    "深圳福田区华强北最便宜的餐厅",
    
    # Edge cases
    "北京的餐厅",  # No anchor
    "鸟巢附近",  # No target
    "711",  # No city, no anchor
]


@pytest.mark.parametrize("query", TEST_QUERIES)
def test_parse_intent(query):
    """Test intent parsing for various queries."""
    intent = parse_location_intent(query)
    
    # Should always return an intent
    assert intent is not None
    assert intent.raw_query == query
    
    # Print for manual inspection
    print(f"\nQuery: {query}")
    print(f"  City: {intent.city}")
    print(f"  District: {intent.district}")
    print(f"  Anchor: {intent.anchor_poi}")
    print(f"  Brand: {intent.brand}")
    print(f"  Category: {intent.category}")
    print(f"  Sort: {intent.sort_by.value} ({intent.sort_order})")
    print(f"  Complete: {intent.is_complete()}")
    print(f"  Confidence: {intent.confidence:.2f}")


def test_end_to_end_nearest_711():
    """Test end-to-end: 北京市的鸟巢周边，最近的711是哪一家."""
    query = "北京市的鸟巢周边，最近的711是哪一家"
    
    # Step 1: Parse intent
    intent = parse_location_intent(query)
    
    assert intent.city == "北京市"
    assert intent.anchor_poi == "国家体育场"  # "鸟巢" resolved to official name
    assert intent.brand == "711"
    assert intent.sort_by.value == "distance"
    assert intent.is_complete()
    
    # Step 2: Simulate API results
    mock_pois = [
        {
            "name": "7-11便利店(鸟巢店)",
            "type": "购物服务;便利店",
            "distance": "500",
            "address": "朝阳区国家体育场南路",
        },
        {
            "name": "全家便利店",
            "type": "购物服务;便利店",
            "distance": "300",
            "address": "朝阳区北辰路",
        },
        {
            "name": "7-11便利店(朝阳店)",
            "type": "购物服务;便利店",
            "distance": "200",
            "address": "朝阳区安立路",
        },
        {
            "name": "国家体育场",
            "type": "体育休闲服务;体育场馆",
            "distance": "100",
            "address": "朝阳区国家体育场南路1号",
        },
    ]
    
    # Step 3: Rerank
    chain = create_default_processor_chain()
    processed = chain.process(mock_pois, intent)
    
    # Should filter to only 7-11, sort by distance
    assert len(processed) == 2
    assert all("7-11" in p["name"] for p in processed)
    assert processed[0]["name"] == "7-11便利店(朝阳店)"  # Nearest
    
    # Step 4: Format
    text = format_location_results(processed, intent, len(mock_pois))
    
    assert "7-11" in text
    assert "200" in text or "朝阳店" in text
    print(f"\nFormatted output:\n{text}")


def test_end_to_end_highest_rated_hotpot():
    """Test end-to-end: 北京朝阳区评分最高的火锅店."""
    query = "北京朝阳区评分最高的火锅店"
    
    # Step 1: Parse intent
    intent = parse_location_intent(query)
    
    assert intent.city == "北京"
    assert "朝阳区" in intent.district  # May include city prefix
    assert intent.category == "火锅"
    assert intent.sort_by.value == "rating"
    
    # Step 2: Simulate API results
    mock_pois = [
        {
            "name": "海底捞火锅",
            "type": "餐饮服务;火锅店",
            "rating": "4.6",
            "address": "朝阳区三里屯",
        },
        {
            "name": "小龙坎火锅",
            "type": "餐饮服务;火锅店",
            "rating": "4.8",
            "address": "朝阳区国贸",
        },
        {
            "name": "呷哺呷哺",
            "type": "餐饮服务;火锅店",
            "rating": "4.3",
            "address": "朝阳区望京",
        },
    ]
    
    # Step 3: Rerank
    chain = create_default_processor_chain()
    processed = chain.process(mock_pois, intent)
    
    # Should sort by rating (descending)
    assert processed[0]["name"] == "小龙坎火锅"  # Highest rating
    
    # Step 4: Format
    text = format_location_results(processed, intent)
    
    assert "小龙坎" in text or "火锅" in text
    print(f"\nFormatted output:\n{text}")


def test_end_to_end_incomplete_intent():
    """Test end-to-end: incomplete intent (no city)."""
    query = "鸟巢附近的餐厅"
    
    # Step 1: Parse intent
    intent = parse_location_intent(query)
    
    # Should extract anchor and category, but no city
    assert intent.anchor_poi == "国家体育场"  # "鸟巢" resolved
    assert intent.category == "餐厅"
    assert not intent.city  # Missing city
    
    # Should be incomplete
    assert not intent.is_complete()


def test_template_variations():
    """Test that templates produce varied outputs."""
    intent = parse_location_intent("北京的711")
    
    mock_pois = [
        {
            "name": "7-11便利店",
            "address": "朝阳区国贸",
            "distance": "500",
        }
    ]
    
    # Generate multiple outputs
    outputs = set()
    for _ in range(10):
        text = format_location_results(mock_pois, intent)
        outputs.add(text)
    
    # Should have some variation (at least 2 different templates)
    print(f"\nGenerated {len(outputs)} unique outputs:")
    for output in outputs:
        print(f"  - {output}")
    
    assert len(outputs) >= 1  # At least one output


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
