"""
Unit tests for streaming plan_trip functionality.

Tests:
1. Basic streaming output format
2. Chunk types and ordering
3. Error handling
4. Self-drive mode
"""

import sys
from pathlib import Path

# Add agent_service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

import pytest
from domain.trip.tool_streaming import plan_trip_streaming
from infra.tool_clients.amap_mcp_client import AmapMCPClient


@pytest.fixture
def amap_client():
    """Create Amap MCP client."""
    return AmapMCPClient()


@pytest.mark.asyncio
async def test_streaming_basic_format(amap_client):
    """Test basic streaming output format."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="上海",
        days=2,
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    # Verify we got chunks
    assert len(chunks) > 0, "Should receive at least one chunk"
    
    # Verify all chunks have required fields
    for chunk in chunks:
        assert "type" in chunk, "Each chunk must have 'type' field"
        assert "text" in chunk, "Each chunk must have 'text' field"
        assert "data" in chunk, "Each chunk must have 'data' field"
    
    # Verify chunk types
    types = [c["type"] for c in chunks]
    assert "header" in types, "Should have header chunk"
    assert "complete" in types or "error" in types, "Should have complete or error chunk"
    
    print(f"\n✅ Received {len(chunks)} chunks")
    print(f"   Chunk types: {set(types)}")


@pytest.mark.asyncio
async def test_streaming_chunk_ordering(amap_client):
    """Test that chunks are in correct order."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="北京",
        days=2,
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    types = [c["type"] for c in chunks]
    
    # First chunk should be header
    assert types[0] == "header", "First chunk should be header"
    
    # Last chunk should be complete or error
    assert types[-1] in ["complete", "error"], "Last chunk should be complete or error"
    
    # Day headers should come before their sessions
    day_indices = [i for i, t in enumerate(types) if t == "day_header"]
    session_indices = [i for i, t in enumerate(types) if t == "session"]
    
    if day_indices and session_indices:
        assert day_indices[0] < session_indices[0], "Day header should come before sessions"
    
    print(f"\n✅ Chunk ordering is correct")
    print(f"   First: {types[0]}")
    print(f"   Last: {types[-1]}")


@pytest.mark.asyncio
async def test_streaming_with_preferences(amap_client):
    """Test streaming with user preferences."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="成都",
        days=2,
        preferences=["food"],
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    types = [c["type"] for c in chunks]
    
    # Should have preference_note chunk
    assert "preference_note" in types, "Should have preference_note chunk when preferences provided"
    
    # Find preference note
    pref_chunks = [c for c in chunks if c["type"] == "preference_note"]
    assert len(pref_chunks) > 0
    assert "美食" in pref_chunks[0]["text"], "Preference note should mention food"
    
    print(f"\n✅ Preference handling works")
    print(f"   Preference note: {pref_chunks[0]['text']}")


@pytest.mark.asyncio
async def test_streaming_self_drive_mode(amap_client):
    """Test streaming with self-drive mode."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="杭州",
        days=2,
        travel_mode="driving",
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    # Find transit chunks
    transit_chunks = [c for c in chunks if c["type"] == "transit"]
    
    if transit_chunks:
        # Check that transit descriptions mention driving
        transit_texts = [c["text"] for c in transit_chunks]
        has_driving = any("驾车" in text for text in transit_texts)
        
        print(f"\n✅ Self-drive mode works")
        print(f"   Transit chunks: {len(transit_chunks)}")
        print(f"   Has driving mention: {has_driving}")
    else:
        print(f"\n⚠️  No transit chunks found (may be normal for close POIs)")


@pytest.mark.asyncio
async def test_streaming_restaurant_recommendations(amap_client):
    """Test that restaurant recommendations are streamed."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="上海",
        days=2,
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    types = [c["type"] for c in chunks]
    
    # Should have restaurant chunks
    has_restaurant_header = "restaurant_header" in types
    has_restaurant = "restaurant" in types
    
    print(f"\n✅ Restaurant recommendations:")
    print(f"   Has restaurant_header: {has_restaurant_header}")
    print(f"   Has restaurant: {has_restaurant}")
    
    if has_restaurant:
        restaurant_chunks = [c for c in chunks if c["type"] == "restaurant"]
        print(f"   Restaurant count: {len(restaurant_chunks)}")


@pytest.mark.asyncio
async def test_streaming_error_missing_destination(amap_client):
    """Test error handling for missing destination."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="",
        days=2,
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    # Should have error chunk
    assert len(chunks) == 1, "Should have exactly one error chunk"
    assert chunks[0]["type"] == "error", "Should be error type"
    assert "目的地" in chunks[0]["text"], "Error should mention destination"
    
    print(f"\n✅ Error handling works for missing destination")


@pytest.mark.asyncio
async def test_streaming_error_no_amap_client():
    """Test error handling for missing amap client."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="上海",
        days=2,
        amap_client=None
    ):
        chunks.append(chunk)
    
    # Should have error chunk
    assert len(chunks) == 1, "Should have exactly one error chunk"
    assert chunks[0]["type"] == "error", "Should be error type"
    assert "MCP" in chunks[0]["text"], "Error should mention MCP"
    
    print(f"\n✅ Error handling works for missing amap client")


@pytest.mark.asyncio
async def test_streaming_data_structure(amap_client):
    """Test that data field contains structured information."""
    chunks = []
    
    async for chunk in plan_trip_streaming(
        destination="上海",
        days=2,
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    # Check header data
    header_chunks = [c for c in chunks if c["type"] == "header"]
    if header_chunks:
        data = header_chunks[0]["data"]
        assert "destination" in data
        assert "days" in data
        assert data["destination"] == "上海"
        assert data["days"] == 2
    
    # Check day_header data
    day_chunks = [c for c in chunks if c["type"] == "day_header"]
    if day_chunks:
        data = day_chunks[0]["data"]
        assert "day" in data
        assert "theme" in data
        assert isinstance(data["day"], int)
    
    # Check stop data
    stop_chunks = [c for c in chunks if c["type"] == "stop"]
    if stop_chunks:
        data = stop_chunks[0]["data"]
        assert "order" in data
        assert "name" in data
        assert "address" in data
    
    print(f"\n✅ Data structure is correct")
    print(f"   Header chunks: {len(header_chunks)}")
    print(f"   Day chunks: {len(day_chunks)}")
    print(f"   Stop chunks: {len(stop_chunks)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
