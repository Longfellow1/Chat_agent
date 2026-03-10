"""M5.1 端到端测试：默认餐厅推荐功能

测试目标：
1. 验证每天行程都包含晚餐推荐
2. 验证餐厅推荐数量为3个
3. 验证餐厅推荐位置合理（靠近当天最后一个景点）
4. 验证API调用量控制（单次city搜索复用）

测试覆盖：
- 10个城市 × 2种模式（公交/自驾）= 20条测试
"""

import pytest
import asyncio
from domain.trip.tool import plan_trip
from infra.tool_clients.amap_mcp_client import AmapMCPClient


@pytest.fixture
def amap_client():
    """Create Amap MCP client."""
    return AmapMCPClient()


# 测试数据：10个城市 × 2种模式
TEST_CASES = [
    # 城市, 天数, 模式
    ("杭州", 3, "transit"),
    ("杭州", 3, "driving"),
    ("南京", 2, "transit"),
    ("南京", 2, "driving"),
    ("苏州", 3, "transit"),
    ("苏州", 3, "driving"),
    ("成都", 4, "transit"),
    ("成都", 4, "driving"),
    ("西安", 3, "transit"),
    ("西安", 3, "driving"),
    ("重庆", 3, "transit"),
    ("重庆", 3, "driving"),
    ("厦门", 2, "transit"),
    ("厦门", 2, "driving"),
    ("青岛", 3, "transit"),
    ("青岛", 3, "driving"),
    ("长沙", 2, "transit"),
    ("长沙", 2, "driving"),
    ("武汉", 3, "transit"),
    ("武汉", 3, "driving"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("destination,days,travel_mode", TEST_CASES)
async def test_dinner_recommendations(destination, days, travel_mode, amap_client):
    """测试餐厅推荐功能"""
    
    # 调用plan_trip
    result = await plan_trip(
        destination=destination,
        days=days,
        travel_mode=travel_mode,
        amap_client=amap_client
    )
    
    # 验证基本成功
    assert result.ok, f"plan_trip failed: {result.error}"
    assert result.raw is not None
    
    # 获取行程数据
    itinerary_data = result.raw.get("itinerary", {})
    day_plans = itinerary_data.get("itinerary", [])
    
    # 验证每天都有餐厅推荐
    for day_plan in day_plans:
        day_num = day_plan["day"]
        dinner_recs = day_plan.get("dinner_recommendations")
        
        # 验证餐厅推荐存在
        assert dinner_recs is not None, f"Day {day_num}: No dinner_recommendations field"
        assert len(dinner_recs) > 0, f"Day {day_num}: Empty dinner_recommendations"
        
        # 验证餐厅推荐数量（应该是3个，或者少于3个如果城市餐厅不足）
        assert len(dinner_recs) <= 3, f"Day {day_num}: Too many dinner recommendations ({len(dinner_recs)})"
        
        # 验证每个餐厅推荐的结构
        for idx, restaurant in enumerate(dinner_recs):
            assert "name" in restaurant, f"Day {day_num}, Restaurant {idx}: Missing 'name' field"
            assert restaurant["name"], f"Day {day_num}, Restaurant {idx}: Empty name"
    
    # 验证输出文本包含餐厅推荐
    assert "晚餐推荐" in result.text or "餐厅" in result.text, \
        f"Output text does not mention dinner recommendations: {result.text}"
    
    print(f"\n✅ {destination} {days}日游 ({travel_mode})")
    print(f"   行程天数: {len(day_plans)}")
    for day_plan in day_plans:
        dinner_count = len(day_plan.get("dinner_recommendations", []))
        print(f"   第{day_plan['day']}天: {dinner_count}个餐厅推荐")


@pytest.mark.asyncio
async def test_api_call_count(amap_client):
    """测试API调用量控制
    
    验证：5日游应该只调用1次餐厅搜索API（city-wide search）
    """
    
    # 使用mock计数器
    original_call_tool = amap_client.call_tool_async
    call_count = {"attractions": 0, "restaurants": 0}
    
    async def mock_call_tool(tool_name, args):
        # 统计API调用
        keywords = args.get("keywords", "")
        if "景点" in keywords:
            call_count["attractions"] += 1
        elif "美食餐厅" in keywords or "餐厅" in keywords:
            call_count["restaurants"] += 1
        
        # 调用原始方法
        return await original_call_tool(tool_name, args)
    
    # 替换方法
    amap_client.call_tool_async = mock_call_tool
    
    # 执行5日游规划
    result = await plan_trip(
        destination="杭州",
        days=5,
        travel_mode="transit",
        amap_client=amap_client
    )
    
    # 验证成功
    assert result.ok, f"plan_trip failed: {result.error}"
    
    # 验证API调用量
    print(f"\n📊 API调用统计（5日游）:")
    print(f"   景点搜索: {call_count['attractions']}次")
    print(f"   餐厅搜索: {call_count['restaurants']}次")
    
    # 餐厅搜索应该只调用1次（city-wide search复用）
    assert call_count["restaurants"] == 1, \
        f"Expected 1 restaurant API call, got {call_count['restaurants']}"
    
    # 景点搜索应该只调用1次
    assert call_count["attractions"] == 1, \
        f"Expected 1 attraction API call, got {call_count['attractions']}"
    
    print("✅ API调用量控制正常")


@pytest.mark.asyncio
async def test_dinner_location_relevance(amap_client):
    """测试餐厅推荐位置相关性
    
    验证：推荐的餐厅应该靠近当天最后一个景点
    """
    
    result = await plan_trip(
        destination="杭州",
        days=3,
        travel_mode="transit",
        amap_client=amap_client
    )
    
    assert result.ok, f"plan_trip failed: {result.error}"
    
    itinerary_data = result.raw.get("itinerary", {})
    day_plans = itinerary_data.get("itinerary", [])
    
    for day_plan in day_plans:
        day_num = day_plan["day"]
        sessions = day_plan.get("sessions", [])
        
        # 找到最后一个stop
        last_stop = None
        for session in sessions:
            stops = session.get("stops", [])
            if stops:
                last_stop = stops[-1]
        
        if not last_stop:
            continue
        
        # 获取餐厅推荐
        dinner_recs = day_plan.get("dinner_recommendations", [])
        
        # 验证餐厅推荐存在
        assert len(dinner_recs) > 0, f"Day {day_num}: No dinner recommendations"
        
        # 打印位置信息（用于人工验证）
        print(f"\n第{day_num}天:")
        print(f"  最后景点: {last_stop.get('name')} ({last_stop.get('business_area') or last_stop.get('district')})")
        print(f"  餐厅推荐:")
        for restaurant in dinner_recs:
            print(f"    - {restaurant['name']} ({restaurant.get('business_area') or restaurant.get('district')})")
    
    print("\n✅ 餐厅位置相关性测试完成（需人工验证位置合理性）")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
