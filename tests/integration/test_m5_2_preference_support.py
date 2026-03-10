"""M5.2 端到端测试：用户偏好参数支持

测试目标：
1. 验证偏好识别准确率100%
2. 验证偏好POI搜索成功
3. 验证景点类型符合偏好
4. 验证API调用量控制

测试覆盖：
- 5种偏好类型 × 4个城市 = 20条测试
- 额外测试：无偏好、多偏好组合
"""

import pytest
import asyncio
from domain.intents.trip_router import route_trip_intent, PREFERENCE_SIGNALS
from domain.trip.tool import plan_trip
from infra.tool_clients.amap_mcp_client import AmapMCPClient


@pytest.fixture
def amap_client():
    """Create Amap MCP client."""
    return AmapMCPClient()


# 测试数据：5种偏好 × 4个城市 = 20条
PREFERENCE_TEST_CASES = [
    # (查询, 期望目的地, 期望天数, 期望偏好)
    ("帮我规划一个吃吃吃的上海2日游", "上海", 2, ["food"]),
    ("北京美食3日游", "北京", 3, ["food"]),
    ("成都吃货之旅2天", "成都", 2, ["food"]),
    ("广州品尝美食3日游", "广州", 3, ["food"]),
    
    ("上海娱乐2日游", "上海", 2, ["entertainment"]),
    ("北京玩乐3天", "北京", 3, ["entertainment"]),
    ("深圳夜生活2日游", "深圳", 2, ["entertainment"]),
    ("成都玩玩玩3天", "成都", 3, ["entertainment"]),
    
    ("杭州文化3日游", "杭州", 3, ["culture"]),
    ("西安历史古迹2天", "西安", 2, ["culture"]),
    ("南京人文之旅3日游", "南京", 3, ["culture"]),
    ("北京博物馆2日游", "北京", 2, ["culture"]),
    
    ("成都休闲2日游", "成都", 2, ["relax"]),
    ("杭州慢游3天", "杭州", 3, ["relax"]),
    ("苏州悠闲之旅2日游", "苏州", 2, ["relax"]),
    ("厦门放松3天", "厦门", 3, ["relax"]),
    
    ("上海购物2日游", "上海", 2, ["shopping"]),
    ("北京逛街3天", "北京", 3, ["shopping"]),
    ("深圳买买买2日游", "深圳", 2, ["shopping"]),
    ("广州血拼3天", "广州", 3, ["shopping"]),
]


@pytest.mark.parametrize("query,expected_dest,expected_days,expected_prefs", PREFERENCE_TEST_CASES)
def test_preference_recognition(query, expected_dest, expected_days, expected_prefs):
    """测试偏好识别准确率"""
    
    is_trip, params, reason = route_trip_intent(query)
    
    # 验证意图识别
    assert is_trip, f"Failed to recognize trip intent: {reason}"
    
    # 验证参数提取
    assert params["destination"] == expected_dest, \
        f"Expected destination '{expected_dest}', got '{params['destination']}'"
    
    assert params["days"] == expected_days, \
        f"Expected {expected_days} days, got {params['days']}"
    
    # 验证偏好识别
    assert params["preferences"] == expected_prefs, \
        f"Expected preferences {expected_prefs}, got {params['preferences']}"
    
    print(f"✅ {query}")
    print(f"   目的地: {params['destination']}, 天数: {params['days']}, 偏好: {params['preferences']}")


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_dest,expected_days,expected_prefs", PREFERENCE_TEST_CASES)
async def test_preference_poi_search(query, expected_dest, expected_days, expected_prefs, amap_client):
    """测试偏好POI搜索成功"""
    
    # 提取参数
    is_trip, params, reason = route_trip_intent(query)
    assert is_trip, f"Failed to recognize trip intent: {reason}"
    
    # 调用plan_trip
    result = await plan_trip(
        destination=params["destination"],
        days=params["days"],
        travel_mode=params.get("travel_mode", "transit"),
        preferences=params.get("preferences"),
        amap_client=amap_client
    )
    
    # 验证成功
    assert result.ok, f"plan_trip failed: {result.error}"
    assert result.raw is not None
    
    # 获取行程数据
    itinerary_data = result.raw.get("itinerary", {})
    day_plans = itinerary_data.get("itinerary", [])
    
    # 验证有行程
    assert len(day_plans) > 0, "No day plans generated"
    
    # 验证每天有景点
    for day_plan in day_plans:
        sessions = day_plan.get("sessions", [])
        total_stops = sum(len(s.get("stops", [])) for s in sessions)
        assert total_stops > 0, f"Day {day_plan['day']}: No stops"
    
    print(f"\n✅ {query}")
    print(f"   行程天数: {len(day_plans)}")
    for day_plan in day_plans:
        sessions = day_plan.get("sessions", [])
        total_stops = sum(len(s.get("stops", [])) for s in sessions)
        print(f"   第{day_plan['day']}天: {total_stops}个景点")


@pytest.mark.asyncio
async def test_no_preference_default_behavior(amap_client):
    """测试无偏好时的默认行为（M5.1场景）"""
    
    query = "帮我规划上海2日游"
    is_trip, params, reason = route_trip_intent(query)
    
    assert is_trip, f"Failed to recognize trip intent: {reason}"
    assert params["preferences"] == [], "Should have no preferences"
    
    # 调用plan_trip
    result = await plan_trip(
        destination=params["destination"],
        days=params["days"],
        travel_mode=params.get("travel_mode", "transit"),
        preferences=params.get("preferences"),
        amap_client=amap_client
    )
    
    assert result.ok, f"plan_trip failed: {result.error}"
    
    # 验证有餐厅推荐（M5.1功能）
    itinerary_data = result.raw.get("itinerary", {})
    day_plans = itinerary_data.get("itinerary", [])
    
    for day_plan in day_plans:
        dinner_recs = day_plan.get("dinner_recommendations")
        assert dinner_recs is not None, f"Day {day_plan['day']}: No dinner recommendations"
        assert len(dinner_recs) > 0, f"Day {day_plan['day']}: Empty dinner recommendations"
    
    print(f"\n✅ 无偏好场景测试通过")
    print(f"   行程天数: {len(day_plans)}")
    print(f"   每天都有餐厅推荐")


@pytest.mark.asyncio
async def test_multiple_preferences(amap_client):
    """测试多偏好组合"""
    
    query = "上海美食娱乐2日游"
    is_trip, params, reason = route_trip_intent(query)
    
    assert is_trip, f"Failed to recognize trip intent: {reason}"
    assert "food" in params["preferences"], "Should recognize 'food' preference"
    assert "entertainment" in params["preferences"], "Should recognize 'entertainment' preference"
    
    # 调用plan_trip
    result = await plan_trip(
        destination=params["destination"],
        days=params["days"],
        travel_mode=params.get("travel_mode", "transit"),
        preferences=params.get("preferences"),
        amap_client=amap_client
    )
    
    assert result.ok, f"plan_trip failed: {result.error}"
    
    itinerary_data = result.raw.get("itinerary", {})
    day_plans = itinerary_data.get("itinerary", [])
    
    assert len(day_plans) > 0, "No day plans generated"
    
    print(f"\n✅ 多偏好组合测试通过")
    print(f"   偏好: {params['preferences']}")
    print(f"   行程天数: {len(day_plans)}")


@pytest.mark.asyncio
async def test_api_call_count_with_preferences(amap_client):
    """测试带偏好的API调用量控制
    
    验证：双偏好5日游应该只调用3次API（2次POI + 1次餐厅）
    """
    
    # 使用mock计数器
    original_call_tool = amap_client.call_tool_async
    call_log = []
    
    async def mock_call_tool(tool_name, args):
        # 记录所有API调用
        keywords = args.get("keywords", "")
        call_log.append(keywords)
        
        # 调用原始方法
        return await original_call_tool(tool_name, args)
    
    # 替换方法
    amap_client.call_tool_async = mock_call_tool
    
    # 执行双偏好5日游规划
    result = await plan_trip(
        destination="杭州",
        days=5,
        travel_mode="transit",
        preferences=["food", "entertainment"],
        amap_client=amap_client
    )
    
    # 验证成功
    assert result.ok, f"plan_trip failed: {result.error}"
    
    # 分析API调用
    print(f"\n📊 API调用统计（双偏好5日游）:")
    print(f"   调用记录: {call_log}")
    print(f"   总计: {len(call_log)}次")
    
    # 验证API调用量：双偏好（2次）+ 餐厅推荐（1次）= 3次
    assert len(call_log) == 3, \
        f"Expected 3 API calls (2 preferences + 1 restaurant), got {len(call_log)}"
    
    # 验证包含偏好关键词
    assert "美食餐厅" in call_log, "Should have food preference search"
    assert "娱乐场所" in call_log, "Should have entertainment preference search"
    
    # 总计应该≤3次（控制在8次上限内）
    assert len(call_log) <= 3, \
        f"Total API calls {len(call_log)} exceeds budget"
    
    print("✅ API调用量控制正常")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
