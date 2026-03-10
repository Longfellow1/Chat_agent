"""Test 50 real-world location queries."""

import pytest

from agent_service.domain.location.parser import parse_location_intent
from agent_service.domain.location.result_processor import create_default_processor_chain
from agent_service.domain.location.templates import format_location_results


# 50 real-world test queries
TEST_QUERIES_50 = [
    # Basic location + brand (10)
    "北京市的鸟巢周边，最近的711是哪一家",
    "上海世博源附近的星巴克",
    "深圳南山区的全家便利店",
    "广州天河区的肯德基",
    "杭州西湖边的麦当劳",
    "成都春熙路的海底捞",
    "南京夫子庙的必胜客",
    "武汉光谷的屈臣氏",
    "西安钟楼附近的沃尔玛",
    "重庆解放碑的家乐福",
    
    # With sorting (10)
    "北京朝阳区评分最高的火锅店",
    "上海浦东新区最便宜的快餐",
    "深圳福田区最近的地铁站",
    "广州越秀区评分最高的粤菜",
    "杭州滨江区最便宜的咖啡厅",
    "成都锦江区最近的停车场",
    "南京鼓楼区评分最高的日料",
    "武汉江汉区最便宜的酒店",
    "西安雁塔区最近的加油站",
    "重庆渝中区评分最高的川菜",
    
    # Complex queries (10)
    "北京市朝阳区国贸附近，最近的24小时便利店",
    "上海静安寺周边评分最高的咖啡厅",
    "深圳福田区华强北最便宜的餐厅",
    "广州天河区珠江新城最近的银行",
    "杭州西湖区文三路评分最高的火锅",
    "成都高新区天府软件园最近的便利店",
    "南京玄武区新街口最便宜的快餐",
    "武汉洪山区光谷广场评分最高的电影院",
    "西安碑林区小寨最近的药店",
    "重庆江北区观音桥评分最高的烤肉",
    
    # Category only (10)
    "北京的餐厅",
    "上海的咖啡厅",
    "深圳的便利店",
    "广州的酒店",
    "杭州的景点",
    "成都的火锅店",
    "南京的博物馆",
    "武汉的医院",
    "西安的书店",
    "重庆的电影院",
    
    # Edge cases (10)
    "鸟巢附近",  # No category
    "711",  # No city, no anchor
    "北京朝阳区",  # No category, no anchor
    "最近的便利店",  # No city
    "评分最高的餐厅",  # No city
    "三里屯附近的肯德基",  # No city (famous landmark)
    "国贸周边的全家便利店",  # No city
    "鸟巢旁边的麦当劳",  # No city
    "世博源附近的星巴克",  # No city
    "西湖边的餐厅",  # No city
]


@pytest.mark.parametrize("query", TEST_QUERIES_50)
def test_50_queries_parsing(query):
    """Test parsing for 50 real-world queries."""
    intent = parse_location_intent(query)
    
    # Should always return an intent
    assert intent is not None
    assert intent.raw_query == query
    
    # Print for inspection
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"  City: {intent.city or '(missing)'}")
    print(f"  District: {intent.district or '-'}")
    print(f"  Anchor: {intent.anchor_poi or '-'}")
    print(f"  Brand: {intent.brand or '-'}")
    print(f"  Category: {intent.category or '-'}")
    print(f"  Sort: {intent.sort_by.value} ({intent.sort_order})")
    print(f"  Complete: {'✓' if intent.is_complete() else '✗'}")
    print(f"  Confidence: {intent.confidence:.2f}")
    
    # Generate tool args
    if intent.is_complete():
        tool_args = intent.to_tool_args()
        print(f"  Tool Args: {tool_args}")


def test_50_queries_summary():
    """Generate summary statistics for 50 queries."""
    results = {
        "total": len(TEST_QUERIES_50),
        "complete": 0,
        "has_city": 0,
        "has_anchor": 0,
        "has_brand": 0,
        "has_category": 0,
        "has_sort": 0,
        "avg_confidence": 0.0,
    }
    
    confidences = []
    
    for query in TEST_QUERIES_50:
        intent = parse_location_intent(query)
        
        if intent.is_complete():
            results["complete"] += 1
        if intent.city:
            results["has_city"] += 1
        if intent.anchor_poi:
            results["has_anchor"] += 1
        if intent.brand:
            results["has_brand"] += 1
        if intent.category:
            results["has_category"] += 1
        if intent.sort_by.value != "distance" or intent.sort_order != "asc":
            results["has_sort"] += 1
        
        confidences.append(intent.confidence)
    
    results["avg_confidence"] = sum(confidences) / len(confidences)
    
    print(f"\n{'='*60}")
    print("SUMMARY STATISTICS")
    print(f"{'='*60}")
    print(f"Total queries: {results['total']}")
    print(f"Complete intents: {results['complete']} ({results['complete']/results['total']*100:.1f}%)")
    print(f"Has city: {results['has_city']} ({results['has_city']/results['total']*100:.1f}%)")
    print(f"Has anchor: {results['has_anchor']} ({results['has_anchor']/results['total']*100:.1f}%)")
    print(f"Has brand: {results['has_brand']} ({results['has_brand']/results['total']*100:.1f}%)")
    print(f"Has category: {results['has_category']} ({results['has_category']/results['total']*100:.1f}%)")
    print(f"Has custom sort: {results['has_sort']} ({results['has_sort']/results['total']*100:.1f}%)")
    print(f"Average confidence: {results['avg_confidence']:.2f}")
    print(f"{'='*60}")
    
    # Assert basic quality metrics
    assert results["complete"] >= 30, "At least 60% should be complete"
    assert results["avg_confidence"] >= 0.5, "Average confidence should be >= 0.5"


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
