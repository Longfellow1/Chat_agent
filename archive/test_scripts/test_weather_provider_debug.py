"""Debug weather provider info"""

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

print(f"Provider chain enabled: {gateway.use_get_weather_chain}")
print(f"Provider chain exists: {gateway.get_weather_chain is not None}")

result = gateway.invoke("get_weather", {"city": "上海"})

print(f"\nResult OK: {result.ok}")
print(f"Result text: {result.text[:100]}")

if result.raw:
    print(f"Provider: {result.raw.get('provider')}")
    print(f"Fallback chain: {result.raw.get('fallback_chain')}")
