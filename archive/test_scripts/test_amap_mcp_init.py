"""检查高德 MCP 初始化状态"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

# 加载 .env.agent
from dotenv import load_dotenv
load_dotenv('.env.agent')

print("=" * 60)
print("环境变量检查")
print("=" * 60)
print(f"AMAP_API_KEY: {os.getenv('AMAP_API_KEY', 'NOT SET')[:20]}...")
print()

from infra.tool_clients.mcp_gateway import MCPToolGateway

print("=" * 60)
print("Gateway 初始化检查")
print("=" * 60)
gateway = MCPToolGateway()
print(f"gateway.amap_key: {gateway.amap_key[:20] if gateway.amap_key else 'NOT SET'}...")
print(f"gateway.amap_mcp: {gateway.amap_mcp}")
print(f"gateway.amap_mcp type: {type(gateway.amap_mcp)}")
print()

if gateway.amap_mcp:
    print("✅ Amap MCP Client 已初始化")
    print(f"   - API Key: {gateway.amap_mcp.api_key[:20]}...")
    print(f"   - Started: {gateway.amap_mcp._started}")
else:
    print("❌ Amap MCP Client 未初始化")
    print("   原因: amap_key 为空或初始化失败")
