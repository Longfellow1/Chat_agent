"""直接测试 Amap MCP Client"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.amap_mcp_client import AmapMCPClient

print("=" * 60)
print("直接测试 Amap MCP Client")
print("=" * 60)

try:
    client = AmapMCPClient()
    print(f"✅ Client 初始化成功")
    print(f"   API Key: {client.api_key[:20]}...")
    print()
    
    print("测试: 上海静安寺附近的咖啡厅")
    print("-" * 60)
    result = client.find_nearby(keyword="咖啡厅", city="上海", location="静安寺")
    
    print(f"Status: {'✅ OK' if result.ok else '❌ FAIL'}")
    print(f"Error: {result.error}")
    print(f"Text: {result.text[:300]}")
    
    if result.raw:
        print(f"Provider: {result.raw.get('provider')}")
        pois = result.raw.get('pois', [])
        print(f"POI Count: {len(pois)}")
        if pois:
            print(f"First POI: {pois[0]}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
