"""
plan_trip 延迟基准测试

测试目标：
1. TTFT（首字延迟）≤ 2s
2. 完整行程生成 ≤ 10s
3. 各阶段延迟分解

执行方式：
  python -m pytest tests/performance/test_plan_trip_latency.py -v -s
"""

import pytest
import time
import asyncio
from domain.trip.tool import plan_trip
from infra.tool_clients.amap_mcp_client import AmapMCPClient


@pytest.fixture
def amap_client():
    """Create Amap MCP client."""
    return AmapMCPClient()


# ============ 基准测试用例 ============

BENCHMARK_CASES = [
    # (查询描述, destination, days, travel_mode, preferences)
    ("标准2日游", "上海", 2, "transit", None),
    ("自驾2日游", "杭州", 2, "driving", None),
    ("美食偏好2日游", "成都", 2, "transit", ["food"]),
    ("文化偏好3日游", "北京", 3, "transit", ["culture"]),
    ("双偏好2日游", "西安", 2, "transit", ["food", "culture"]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("desc,destination,days,travel_mode,preferences", BENCHMARK_CASES)
async def test_total_latency_benchmark(desc, destination, days, travel_mode, preferences, amap_client):
    """测试完整行程生成延迟 ≤ 10s"""
    
    print(f"\n{'='*60}")
    print(f"测试用例: {desc}")
    print(f"参数: destination={destination}, days={days}, mode={travel_mode}, prefs={preferences}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    result = await plan_trip(
        destination=destination,
        days=days,
        travel_mode=travel_mode,
        preferences=preferences,
        amap_client=amap_client
    )
    
    total_latency = time.time() - start_time
    
    # 验证结果
    assert result.ok, f"plan_trip失败: {result.error}"
    
    # 验证延迟
    print(f"\n⏱️  总延迟: {total_latency:.2f}s")
    
    if total_latency <= 10.0:
        print(f"✅ 延迟达标（≤ 10s）")
    else:
        print(f"❌ 延迟超标（> 10s）")
    
    assert total_latency <= 10.0, f"总延迟 {total_latency:.2f}s 超过10秒目标"
    
    # 输出统计
    itinerary_data = result.raw.get("itinerary", {})
    day_plans = itinerary_data.get("itinerary", [])
    
    total_pois = sum(
        len(stop)
        for day in day_plans
        for session in day.get("sessions", [])
        for stop in session.get("stops", [])
    )
    
    print(f"📊 统计:")
    print(f"   - 天数: {days}")
    print(f"   - 景点数: {total_pois}")
    print(f"   - 平均每天: {total_pois/days:.1f}个")
    print(f"   - 平均每景点: {total_latency/total_pois:.2f}s")


@pytest.mark.asyncio
async def test_latency_breakdown(amap_client):
    """测试延迟分解（各阶段耗时）"""
    
    print(f"\n{'='*60}")
    print(f"延迟分解测试")
    print(f"{'='*60}")
    
    destination = "上海"
    days = 2
    
    # 阶段1: POI搜索
    from domain.trip.engine import TripPlannerEngine
    engine = TripPlannerEngine(amap_client)
    
    start = time.time()
    pois = await engine._search_attractions(destination)
    poi_search_time = time.time() - start
    
    print(f"\n⏱️  阶段1 - POI搜索: {poi_search_time:.2f}s")
    print(f"   找到 {len(pois)} 个景点")
    
    # 阶段2: 地理聚类
    start = time.time()
    clusters = engine.clusterer.cluster(pois, days, "transit")
    cluster_time = time.time() - start
    
    print(f"⏱️  阶段2 - 地理聚类: {cluster_time:.2f}s")
    print(f"   聚类为 {len(clusters)} 天")
    
    # 阶段3: 时段分配
    start = time.time()
    itinerary = engine._allocate_to_sessions(clusters, days)
    allocate_time = time.time() - start
    
    print(f"⏱️  阶段3 - 时段分配: {allocate_time:.2f}s")
    
    # 阶段4: 交通估算
    start = time.time()
    itinerary = engine._estimate_transit_times(itinerary, "transit")
    transit_time = time.time() - start
    
    print(f"⏱️  阶段4 - 交通估算: {transit_time:.2f}s")
    
    # 阶段5: 餐厅推荐
    start = time.time()
    await engine._add_dinner_recommendations(itinerary, destination)
    restaurant_time = time.time() - start
    
    print(f"⏱️  阶段5 - 餐厅推荐: {restaurant_time:.2f}s")
    
    # 总计
    total = poi_search_time + cluster_time + allocate_time + transit_time + restaurant_time
    
    print(f"\n📊 延迟分解:")
    print(f"   POI搜索:   {poi_search_time:.2f}s ({poi_search_time/total*100:.1f}%)")
    print(f"   地理聚类:   {cluster_time:.2f}s ({cluster_time/total*100:.1f}%)")
    print(f"   时段分配:   {allocate_time:.2f}s ({allocate_time/total*100:.1f}%)")
    print(f"   交通估算:   {transit_time:.2f}s ({transit_time/total*100:.1f}%)")
    print(f"   餐厅推荐:   {restaurant_time:.2f}s ({restaurant_time/total*100:.1f}%)")
    print(f"   ─────────────────────────")
    print(f"   总计:       {total:.2f}s")
    
    # 识别瓶颈
    stages = {
        "POI搜索": poi_search_time,
        "地理聚类": cluster_time,
        "时段分配": allocate_time,
        "交通估算": transit_time,
        "餐厅推荐": restaurant_time,
    }
    
    bottleneck = max(stages.items(), key=lambda x: x[1])
    print(f"\n🔍 性能瓶颈: {bottleneck[0]} ({bottleneck[1]:.2f}s)")
    
    if bottleneck[1] > 3.0:
        print(f"⚠️  建议优化 {bottleneck[0]} 阶段")


@pytest.mark.asyncio
async def test_concurrent_requests(amap_client):
    """测试并发请求性能"""
    
    print(f"\n{'='*60}")
    print(f"并发请求测试")
    print(f"{'='*60}")
    
    # 模拟3个并发请求
    tasks = [
        plan_trip("上海", 2, "transit", None, amap_client),
        plan_trip("北京", 2, "transit", None, amap_client),
        plan_trip("杭州", 2, "transit", None, amap_client),
    ]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start
    
    # 验证所有请求成功
    for i, result in enumerate(results, 1):
        assert result.ok, f"请求{i}失败: {result.error}"
    
    print(f"\n⏱️  3个并发请求总耗时: {total_time:.2f}s")
    print(f"   平均每个请求: {total_time/3:.2f}s")
    
    if total_time <= 15.0:
        print(f"✅ 并发性能良好")
    else:
        print(f"⚠️  并发性能需要优化")


@pytest.mark.asyncio
async def test_cache_effectiveness(amap_client):
    """测试缓存效果（如果实现了缓存）"""
    
    print(f"\n{'='*60}")
    print(f"缓存效果测试")
    print(f"{'='*60}")
    
    destination = "上海"
    days = 2
    
    # 第一次请求（冷启动）
    start = time.time()
    result1 = await plan_trip(destination, days, "transit", None, amap_client)
    cold_time = time.time() - start
    
    assert result1.ok
    print(f"⏱️  冷启动: {cold_time:.2f}s")
    
    # 第二次请求（可能命中缓存）
    start = time.time()
    result2 = await plan_trip(destination, days, "transit", None, amap_client)
    warm_time = time.time() - start
    
    assert result2.ok
    print(f"⏱️  热启动: {warm_time:.2f}s")
    
    # 计算加速比
    if warm_time < cold_time:
        speedup = cold_time / warm_time
        print(f"✅ 缓存加速: {speedup:.2f}x")
    else:
        print(f"⚠️  未检测到缓存效果")


# ============ 压力测试 ============

@pytest.mark.asyncio
@pytest.mark.slow
async def test_stress_10_requests(amap_client):
    """压力测试：10个连续请求"""
    
    print(f"\n{'='*60}")
    print(f"压力测试：10个连续请求")
    print(f"{'='*60}")
    
    latencies = []
    
    for i in range(10):
        start = time.time()
        result = await plan_trip("上海", 2, "transit", None, amap_client)
        latency = time.time() - start
        
        assert result.ok, f"请求{i+1}失败"
        latencies.append(latency)
        
        print(f"请求{i+1}: {latency:.2f}s")
    
    # 统计
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    
    print(f"\n📊 统计:")
    print(f"   平均延迟: {avg_latency:.2f}s")
    print(f"   最大延迟: {max_latency:.2f}s")
    print(f"   最小延迟: {min_latency:.2f}s")
    
    # 验证稳定性
    assert avg_latency <= 10.0, f"平均延迟超标: {avg_latency:.2f}s"
    assert max_latency <= 15.0, f"最大延迟超标: {max_latency:.2f}s"
    
    print(f"✅ 压力测试通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
