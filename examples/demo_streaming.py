"""
Demo script for streaming plan_trip output.

Usage:
    python examples/demo_streaming.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent_service"))

import asyncio
import time
from domain.trip.tool_streaming import plan_trip_streaming
from infra.tool_clients.amap_mcp_client import AmapMCPClient


async def demo_streaming(destination: str, days: int = 2, travel_mode: str = "transit"):
    """Demo streaming output."""
    print(f"\n{'='*60}")
    print(f"流式输出演示: {destination}{days}日游")
    print(f"{'='*60}\n")
    
    amap_client = AmapMCPClient()
    
    start_time = time.time()
    ttft = None
    chunk_count = 0
    
    async for chunk in plan_trip_streaming(
        destination=destination,
        days=days,
        travel_mode=travel_mode,
        amap_client=amap_client
    ):
        # Measure TTFT
        if ttft is None:
            ttft = time.time() - start_time
        
        chunk_count += 1
        
        # Print chunk
        chunk_type = chunk["type"]
        text = chunk["text"]
        
        # Color coding
        if chunk_type == "header":
            print(f"\033[1;36m{text}\033[0m", end="", flush=True)
        elif chunk_type == "day_header":
            print(f"\033[1;32m{text}\033[0m", end="", flush=True)
        elif chunk_type == "session":
            print(f"\033[1;33m{text}\033[0m", end="", flush=True)
        elif chunk_type == "stop":
            print(f"{text}", end="", flush=True)
        elif chunk_type == "transit":
            print(f"\033[0;90m{text}\033[0m", end="", flush=True)
        elif chunk_type == "restaurant_header":
            print(f"\033[1;35m{text}\033[0m", end="", flush=True)
        elif chunk_type == "restaurant":
            print(f"{text}", end="", flush=True)
        elif chunk_type == "error":
            print(f"\033[1;31m❌ {text}\033[0m", end="", flush=True)
        
        # Add newline after each chunk
        print()
        
        # Simulate streaming delay (optional)
        # await asyncio.sleep(0.05)
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"性能指标:")
    print(f"  TTFT (首字延迟): {ttft:.2f}s")
    print(f"  总延迟: {total_time:.2f}s")
    print(f"  流式块数: {chunk_count}")
    print(f"  平均每块: {total_time/chunk_count:.3f}s")
    print(f"{'='*60}\n")


async def main():
    """Run demos."""
    # Demo 1: Standard 2-day trip
    await demo_streaming("上海", 2, "transit")
    
    # Demo 2: Self-drive trip
    # await demo_streaming("杭州", 2, "driving")
    
    # Demo 3: 3-day trip
    # await demo_streaming("北京", 3, "transit")


if __name__ == "__main__":
    asyncio.run(main())
