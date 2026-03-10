"""
Integration tests for streaming API endpoint.

Tests:
1. /chat/stream endpoint basic functionality
2. TTFT (Time To First Token) measurement
3. Total latency measurement
4. SSE format validation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

import pytest
import time
import json
from fastapi.testclient import TestClient
from app.api.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_streaming_endpoint_exists(client):
    """Test that /chat/stream endpoint exists."""
    response = client.post(
        "/chat/stream",
        json={"query": "帮我规划上海2日游"}
    )
    
    # Should not return 404
    assert response.status_code != 404, "/chat/stream endpoint should exist"
    
    print(f"\n✅ /chat/stream endpoint exists")
    print(f"   Status code: {response.status_code}")


def test_streaming_basic_flow(client):
    """Test basic streaming flow."""
    with client.stream("POST", "/chat/stream", json={"query": "帮我规划上海2日游"}) as response:
        assert response.status_code == 200, "Should return 200 OK"
        
        # Collect chunks
        chunks = []
        for line in response.iter_lines():
            if line:
                line_str = line.strip()
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix
                    chunk = json.loads(data_str)
                    chunks.append(chunk)
    
    # Verify we got chunks
    assert len(chunks) > 0, "Should receive at least one chunk"
    
    # Verify chunk structure
    for chunk in chunks:
        assert "type" in chunk, "Each chunk must have 'type' field"
        assert "text" in chunk, "Each chunk must have 'text' field"
    
    # Verify first and last chunks
    assert chunks[0]["type"] == "header", "First chunk should be header"
    assert chunks[-1]["type"] in ["complete", "error"], "Last chunk should be complete or error"
    
    print(f"\n✅ Basic streaming flow works")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   First chunk type: {chunks[0]['type']}")
    print(f"   Last chunk type: {chunks[-1]['type']}")


def test_streaming_ttft_measurement(client):
    """Test TTFT (Time To First Token) measurement."""
    start_time = time.time()
    
    with client.stream("POST", "/chat/stream", json={"query": "帮我规划北京2日游"}) as response:
        assert response.status_code == 200
        
        # Measure time to first chunk
        ttft = None
        chunk_count = 0
        
        for line in response.iter_lines():
            if line:
                line_str = line.strip()
                if line_str.startswith("data: "):
                    if ttft is None:
                        ttft = time.time() - start_time
                    chunk_count += 1
    
    assert ttft is not None, "Should receive at least one chunk"
    
    print(f"\n⏱️  TTFT Measurement:")
    print(f"   TTFT: {ttft:.2f}s")
    print(f"   Total chunks: {chunk_count}")
    
    # Verify TTFT target
    if ttft <= 2.0:
        print(f"   ✅ TTFT达标 (≤ 2s)")
    else:
        print(f"   ⚠️  TTFT超标 (> 2s)")
    
    # Note: We don't assert here because TTFT may vary with network/API conditions
    # This is a measurement test, not a strict validation


def test_streaming_total_latency(client):
    """Test total latency measurement."""
    start_time = time.time()
    
    with client.stream("POST", "/chat/stream", json={"query": "帮我规划杭州2日游"}) as response:
        assert response.status_code == 200
        
        # Consume all chunks
        chunk_count = 0
        for line in response.iter_lines():
            if line:
                line_str = line.strip()
                if line_str.startswith("data: "):
                    chunk_count += 1
    
    total_latency = time.time() - start_time
    
    print(f"\n⏱️  Total Latency Measurement:")
    print(f"   Total latency: {total_latency:.2f}s")
    print(f"   Total chunks: {chunk_count}")
    print(f"   Avg per chunk: {total_latency/chunk_count:.3f}s")
    
    # Verify total latency target
    if total_latency <= 10.0:
        print(f"   ✅ 总延迟达标 (≤ 10s)")
    else:
        print(f"   ⚠️  总延迟超标 (> 10s)")


def test_streaming_self_drive_mode(client):
    """Test streaming with self-drive mode."""
    with client.stream("POST", "/chat/stream", json={"query": "我想自驾游去苏州玩2天"}) as response:
        assert response.status_code == 200
        
        # Collect chunks
        chunks = []
        for line in response.iter_lines():
            if line:
                line_str = line.strip()
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    chunk = json.loads(data_str)
                    chunks.append(chunk)
    
    # Verify we got chunks
    assert len(chunks) > 0
    
    # Check for transit chunks
    transit_chunks = [c for c in chunks if c["type"] == "transit"]
    
    print(f"\n✅ Self-drive mode streaming works")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Transit chunks: {len(transit_chunks)}")


def test_streaming_sse_format(client):
    """Test SSE (Server-Sent Events) format."""
    with client.stream("POST", "/chat/stream", json={"query": "帮我规划成都2日游"}) as response:
        assert response.status_code == 200
        
        # Verify SSE headers
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify SSE format
        valid_sse_lines = 0
        for line in response.iter_lines():
            if line:
                line_str = line.strip()
                if line_str.startswith("data: "):
                    valid_sse_lines += 1
                    # Verify JSON is valid
                    data_str = line_str[6:]
                    chunk = json.loads(data_str)
                    assert isinstance(chunk, dict)
    
    assert valid_sse_lines > 0, "Should have at least one valid SSE line"
    
    print(f"\n✅ SSE format is correct")
    print(f"   Valid SSE lines: {valid_sse_lines}")


def test_streaming_non_trip_query(client):
    """Test streaming with non-trip query (should fall back to regular flow)."""
    with client.stream("POST", "/chat/stream", json={"query": "今天天气怎么样"}) as response:
        assert response.status_code == 200
        
        # Collect chunks
        chunks = []
        for line in response.iter_lines():
            if line:
                line_str = line.strip()
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    chunk = json.loads(data_str)
                    chunks.append(chunk)
    
    # Should have at least one chunk (complete)
    assert len(chunks) > 0
    
    # Last chunk should be complete
    assert chunks[-1]["type"] == "complete"
    
    print(f"\n✅ Non-trip query fallback works")
    print(f"   Total chunks: {len(chunks)}")


def test_streaming_error_handling(client):
    """Test error handling in streaming."""
    response = client.post(
        "/chat/stream",
        json={"query": ""}  # Empty query
    )
    
    # Should return error status
    assert response.status_code == 422, "Empty query should return validation error"
    
    print(f"\n✅ Error handling works")
    print(f"   Status code: {response.status_code}")


def test_streaming_concurrent_requests(client):
    """Test concurrent streaming requests."""
    import concurrent.futures
    
    def make_request(query):
        with client.stream("POST", "/chat/stream", json={"query": query}) as response:
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.strip()
                    if line_str.startswith("data: "):
                        chunk_count += 1
            
            return response.status_code, chunk_count
    
    # Make 3 concurrent requests
    queries = [
        "帮我规划上海2日游",
        "帮我规划北京2日游",
        "帮我规划杭州2日游"
    ]
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request, q) for q in queries]
        results = [f.result() for f in futures]
    
    total_time = time.time() - start_time
    
    # Verify all requests succeeded
    for status_code, chunk_count in results:
        assert status_code == 200
        assert chunk_count > 0
    
    print(f"\n✅ Concurrent requests work")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Avg per request: {total_time/3:.2f}s")
    print(f"   Results: {results}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
