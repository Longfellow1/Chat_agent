"""Debug provider chain issue"""

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

# Test query
query = {"keyword": "停车场", "city": "上海"}
print(f"Testing: {query}")

result = gateway.invoke("find_nearby", query)

print(f"\nResult OK: {result.ok}")
print(f"Result text: {result.text[:100]}")
print(f"Result error: {result.error}")

if result.raw:
    print(f"Provider: {result.raw.get('provider')}")
    print(f"Fallback chain: {result.raw.get('fallback_chain')}")
    print(f"Has pois: {'pois' in result.raw}")
    
    # Check provider chain usage
    print(f"\nProvider chain enabled: {gateway.use_find_nearby_chain}")
    if hasattr(gateway, 'find_nearby_chain') and gateway.find_nearby_chain:
        print(f"Provider chain exists: True")
    else:
        print(f"Provider chain exists: False")
