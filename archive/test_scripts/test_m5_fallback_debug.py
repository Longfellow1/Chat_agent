"""Debug M5 fallback mechanism."""

import sys
import os
sys.path.insert(0, 'agent_service')

os.environ['AMAP_API_KEY'] = 'REDACTED'
os.environ['BAIDU_MAP_API_KEY'] = 'REDACTED'

from unittest.mock import patch
from infra.tool_clients.mcp_gateway import MCPToolGateway
from infra.tool_clients.providers.amap_mcp_provider import AmapMCPProvider

gateway = MCPToolGateway()

# 模拟高德 MCP 故障
with patch.object(AmapMCPProvider, 'execute', side_effect=TimeoutError("Simulated timeout")):
    result = gateway.invoke("find_nearby", {"keyword": "停车场", "city": "上海"})
    
    print("Result OK:", result.ok)
    print("Provider:", result.raw.get("provider") if result.raw else None)
    print("Fallback chain:", result.raw.get("fallback_chain") if result.raw else None)
    print("Error:", result.error)
    print("Text preview:", result.text[:100] if result.text else None)
