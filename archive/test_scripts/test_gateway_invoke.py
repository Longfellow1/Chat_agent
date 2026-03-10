"""测试 Gateway.invoke() 方法"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.mcp_gateway import MCPToolGateway

print("=" * 60)
print("测试 Gateway.invoke()")
print("=" * 60)

gateway = MCPToolGateway()

# 测试 invoke 方法
print("调用 gateway.invoke('find_nearby', {...})")
print("-" * 60)

result = gateway.invoke("find_nearby", {
    "keyword": "咖啡厅",
    "city": "上海",
    "location": "静安寺"
})

print(f"Status: {'✅ OK' if result.ok else '❌ FAIL'}")
print(f"Error: {result.error}")
print(f"Text: {result.text[:200]}")

if result.raw:
    print(f"Provider: {result.raw.get('provider')}")
    pois = result.raw.get('pois', [])
    print(f"POI Count: {len(pois)}")
    if pois and len(pois) > 0:
        print(f"First POI name: {pois[0].get('name', 'unknown')}")
        
print()
print("=" * 60)
print("结论")
print("=" * 60)

is_real = result.raw and result.raw.get('provider') == 'amap_mcp'
if is_real:
    print("✅ Gateway.invoke() 返回真实 POI 数据")
else:
    print("❌ Gateway.invoke() 返回 mock 数据")
