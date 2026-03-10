"""测试 Gateway 的 _nearby 方法"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.mcp_gateway import MCPToolGateway

print("=" * 60)
print("测试 Gateway._nearby()")
print("=" * 60)

gateway = MCPToolGateway()

print(f"gateway.amap_mcp: {gateway.amap_mcp}")
print(f"gateway.amap_key: {gateway.amap_key[:20] if gateway.amap_key else 'NOT SET'}...")
print()

# 添加调试：直接调用 _nearby
print("调用 gateway._nearby(keyword='咖啡厅', city='上海', location='静安寺')")
print("-" * 60)

result = gateway._nearby(keyword="咖啡厅", city="上海", location="静安寺")

print(f"Status: {'✅ OK' if result.ok else '❌ FAIL'}")
print(f"Error: {result.error}")
print(f"Text: {result.text[:200]}")

if result.raw:
    print(f"Provider: {result.raw.get('provider')}")
    pois = result.raw.get('pois', [])
    print(f"POI Count: {len(pois)}")
    if pois and len(pois) > 0:
        print(f"First POI name: {pois[0].get('name', 'unknown')}")
