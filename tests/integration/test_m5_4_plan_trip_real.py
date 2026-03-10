"""Integration tests for M5.4 plan_trip with real Amap MCP data."""

import sys
import os
from pathlib import Path

# Load environment variables from .env.agent
env_file = Path(__file__).parent.parent.parent / '.env.agent'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key not in os.environ:  # Don't override existing env vars
                    os.environ[key] = value

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent_service'))

import pytest
import asyncio
import time
from domain.trip.engine import TripPlannerEngine
from infra.tool_clients.amap_mcp_client import AmapMCPClient


@pytest.fixture
def amap_client():
    """Create real Amap MCP client."""
    client = AmapMCPClient()
    yield client
    client.close()


@pytest.fixture
def trip_engine(amap_client):
    """Create trip planner engine with real client."""
    return TripPlannerEngine(amap_client)


@pytest.mark.asyncio
async def test_search_attractions_shanghai(trip_engine):
    """Test searching for real attractions in Shanghai."""
    pois = await trip_engine._search_attractions("上海")
    
    # Verify we got real POIs
    assert len(pois) > 0, "Should find attractions in Shanghai"
    
    # Verify POI structure
    first_poi = pois[0]
    assert "name" in first_poi
    assert "address" in first_poi
    assert first_poi["name"] != "", "POI should have a name"
    
    print(f"\n✅ Found {len(pois)} attractions in Shanghai")
    print(f"First POI: {first_poi['name']} at {first_poi['address']}")


@pytest.mark.asyncio
async def test_plan_trip_shanghai_transit(trip_engine):
    """Test planning a 2-day trip to Shanghai with transit mode."""
    result = await trip_engine.plan("上海", 2, "transit")
    
    # Verify basic structure
    assert result.destination == "上海"
    assert result.days == 2
    assert result.travel_mode == "transit"
    assert len(result.itinerary) > 0
    
    # Verify day plans
    for day_plan in result.itinerary:
        assert day_plan.day > 0
        assert day_plan.theme != ""
        assert len(day_plan.sessions) > 0
        
        # Verify sessions
        for session in day_plan.sessions:
            assert session.period in ["上午", "下午", "晚上"]
            assert len(session.stops) > 0
            
            # Verify stops
            for stop in session.stops:
                assert stop.name != ""
                assert stop.address != ""
                
                # Verify transit info (except last stop)
                if stop.transit_to_next:
                    assert stop.transit_to_next.mode == "transit"
                    assert stop.transit_to_next.duration_minutes > 0
                    assert stop.transit_to_next.description != ""
    
    print(f"\n✅ Generated {len(result.itinerary)}-day itinerary for Shanghai (transit)")
    print(f"Day 1 theme: {result.itinerary[0].theme}")
    print(f"Day 1 sessions: {len(result.itinerary[0].sessions)}")


@pytest.mark.asyncio
async def test_plan_trip_shanghai_driving(trip_engine):
    """Test planning a 2-day trip to Shanghai with driving mode."""
    result = await trip_engine.plan("上海", 2, "driving")
    
    # Verify travel mode
    assert result.travel_mode == "driving"
    
    # Verify transit info uses driving mode
    for day_plan in result.itinerary:
        for session in day_plan.sessions:
            for stop in session.stops:
                if stop.transit_to_next:
                    assert stop.transit_to_next.mode == "driving"
                    assert "驾车" in stop.transit_to_next.description or "分钟" in stop.transit_to_next.description
    
    print(f"\n✅ Generated {len(result.itinerary)}-day itinerary for Shanghai (driving)")


@pytest.mark.asyncio
async def test_plan_trip_beijing(trip_engine):
    """Test planning a trip to Beijing."""
    result = await trip_engine.plan("北京", 2, "transit")
    
    assert result.destination == "北京"
    assert len(result.itinerary) > 0
    
    # Verify we got real Beijing attractions
    first_stop = result.itinerary[0].sessions[0].stops[0]
    assert first_stop.name != ""
    
    print(f"\n✅ Generated itinerary for Beijing")
    print(f"First attraction: {first_stop.name}")


@pytest.mark.asyncio
async def test_plan_trip_hangzhou(trip_engine):
    """Test planning a trip to Hangzhou."""
    result = await trip_engine.plan("杭州", 2, "transit")
    
    assert result.destination == "杭州"
    assert len(result.itinerary) > 0
    
    print(f"\n✅ Generated itinerary for Hangzhou")


@pytest.mark.asyncio
async def test_transit_time_estimation_real_data(trip_engine):
    """Test transit time estimation with real POI data."""
    # Get real POIs from Shanghai
    pois = await trip_engine._search_attractions("上海")
    assert len(pois) >= 2
    
    # Test estimation between first two POIs
    poi_a = pois[0]
    poi_b = pois[1]
    
    transit_info = trip_engine.transit_estimator.estimate(poi_a, poi_b, "transit")
    
    assert transit_info.mode == "transit"
    assert transit_info.duration_minutes > 0
    assert transit_info.description != ""
    
    print(f"\n✅ Transit estimation: {poi_a['name']} → {poi_b['name']}")
    print(f"Duration: {transit_info.duration_minutes} minutes")
    print(f"Description: {transit_info.description}")


@pytest.mark.asyncio
async def test_clustering_real_data(trip_engine):
    """Test POI clustering with real data."""
    # Get real POIs
    pois = await trip_engine._search_attractions("上海")
    assert len(pois) > 0
    
    # Test clustering
    clusters = trip_engine.clusterer.cluster(pois, 2, "transit")
    
    assert len(clusters) == 2
    assert len(clusters[0]) > 0
    
    print(f"\n✅ Clustered {len(pois)} POIs into {len(clusters)} days")
    print(f"Day 1: {len(clusters[0])} POIs")
    print(f"Day 2: {len(clusters[1])} POIs")


@pytest.mark.asyncio
async def test_session_allocation_real_data(trip_engine):
    """Test session allocation with real data."""
    # Get real POIs
    pois = await trip_engine._search_attractions("上海")
    
    # Cluster them
    clusters = trip_engine.clusterer.cluster(pois, 2, "transit")
    
    # Allocate to sessions
    itinerary = trip_engine._allocate_to_sessions(clusters, 2)
    
    assert len(itinerary) > 0
    
    # Verify session allocation
    for day_plan in itinerary:
        total_stops = sum(len(session.stops) for session in day_plan.sessions)
        assert total_stops > 0
        
        # Verify time budgets are respected
        for session in day_plan.sessions:
            total_duration = sum(stop.duration_minutes for stop in session.stops)
            
            if session.period == "上午":
                assert total_duration <= 240  # 4 hours
            elif session.period == "下午":
                assert total_duration <= 240  # 4 hours
            elif session.period == "晚上":
                assert total_duration <= 120  # 2 hours
    
    print(f"\n✅ Allocated POIs to sessions with time budgets")


@pytest.mark.asyncio
async def test_adcode_comparison_logic(trip_engine):
    """Test adcode comparison logic with real data."""
    # Get real POIs from Shanghai
    pois = await trip_engine._search_attractions("上海")
    
    # Find POIs with adcodes
    pois_with_adcode = [poi for poi in pois if poi.get("adcode")]
    
    if len(pois_with_adcode) >= 2:
        poi_a = pois_with_adcode[0]
        poi_b = pois_with_adcode[1]
        
        adcode_a = poi_a["adcode"]
        adcode_b = poi_b["adcode"]
        
        print(f"\n✅ Adcode comparison test:")
        print(f"POI A: {poi_a['name']} - adcode: {adcode_a}")
        print(f"POI B: {poi_b['name']} - adcode: {adcode_b}")
        
        # Verify adcode format (should be 6 digits)
        assert len(adcode_a) == 6, f"Adcode should be 6 digits, got {len(adcode_a)}"
        assert len(adcode_b) == 6, f"Adcode should be 6 digits, got {len(adcode_b)}"
        
        # Test comparison logic
        if adcode_a[:4] == adcode_b[:4]:
            print(f"Same district (first 4 digits match)")
        elif adcode_a[:2] == adcode_b[:2]:
            print(f"Same city, different district (first 2 digits match)")
        else:
            print(f"Different cities")


@pytest.mark.asyncio
async def test_latency_ttft(trip_engine):
    """Test Time To First Token (TTFT) latency."""
    start = time.time()
    
    # Start planning
    result = await trip_engine.plan("上海", 2, "transit")
    
    # In a real streaming scenario, TTFT would be measured when first token is generated
    # For now, we measure total time
    total_time = time.time() - start
    
    print(f"\n✅ Latency test:")
    print(f"Total time: {total_time:.2f}s")
    
    # Verify latency target (≤ 10s for complete generation)
    assert total_time <= 10.0, f"Total time {total_time:.2f}s exceeds 10s target"


@pytest.mark.asyncio
async def test_driving_mode_clustering(trip_engine):
    """Test that driving mode uses different clustering strategy."""
    pois = await trip_engine._search_attractions("上海")
    
    # Test transit mode clustering
    transit_clusters = trip_engine.clusterer.cluster(pois, 2, "transit")
    
    # Test driving mode clustering
    driving_clusters = trip_engine.clusterer.cluster(pois, 2, "driving")
    
    # Both should produce valid clusters
    assert len(transit_clusters) == 2
    assert len(driving_clusters) == 2
    
    print(f"\n✅ Clustering strategy test:")
    print(f"Transit mode: {len(transit_clusters[0])} + {len(transit_clusters[1])} POIs")
    print(f"Driving mode: {len(driving_clusters[0])} + {len(driving_clusters[1])} POIs")


@pytest.mark.asyncio
async def test_empty_destination(trip_engine):
    """Test handling of destination with no POIs."""
    result = await trip_engine.plan("不存在的城市XYZ", 2, "transit")
    
    # Amap may return fallback results, so we just verify the structure is valid
    assert result.destination == "不存在的城市XYZ"
    # May or may not have results depending on Amap's fallback behavior
    
    print(f"\n✅ Empty destination handled: {len(result.itinerary)} days returned")


@pytest.mark.asyncio
async def test_multiple_cities(trip_engine):
    """Test planning trips to multiple cities."""
    cities = ["上海", "北京", "杭州"]
    
    for city in cities:
        result = await trip_engine.plan(city, 2, "transit")
        assert result.destination == city
        assert len(result.itinerary) > 0
        
        print(f"\n✅ {city}: {len(result.itinerary)} days planned")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
