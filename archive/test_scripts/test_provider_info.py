"""Test provider info propagation"""

import sys
import os
from pathlib import Path

# Load env
env_file = Path(__file__).parent / '.env.agent'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent_service'))

from infra.tool_clients.mcp_gateway import MCPToolGateway

gateway = MCPToolGateway()

# Test 3 queries
queries = [
    {"keyword": "停车场", "city": "上海"},
    {"keyword": "餐厅", "city": "北京"},
    {"keyword": "充电桩", "city": "深圳"},
]

print("=== Testing Provider Info ===\n")

for i, query in enumerate(queries, 1):
    result = gateway.invoke("find_nearby", query)
    
    print(f"[{i}] {query['keyword']} @ {query['city']}")
    print(f"  OK: {result.ok}")
    
    if result.raw:
        provider = result.raw.get("provider")
        fallback_chain = result.raw.get("fallback_chain")
        print(f"  Provider: {provider}")
        print(f"  Fallback chain: {fallback_chain}")
    else:
        print(f"  No raw data")
    print()
