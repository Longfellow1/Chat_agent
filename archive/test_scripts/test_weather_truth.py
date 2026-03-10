"""测试天气工具的真实状态"""
import sys
import os
from pathlib import Path

# 加载 .env.agent
env_file = Path('.env.agent')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key not in os.environ:
                    os.environ[key] = value

sys.path.insert(0, 'agent_service')

from infra.tool_clients.mcp_gateway import MCPToolGateway

print("=== 环境变量检查 ===")
print(f"QWEATHER_API_KEY: {os.getenv('QWEATHER_API_KEY', 'NOT SET')[:20]}...")
print(f"QWEATHER_API_HOST: {os.getenv('QWEATHER_API_HOST', 'NOT SET')}")

print("\n=== Gateway 初始化 ===")
gw = MCPToolGateway()
print(f"qweather_key: {gw.qweather_key[:20] if gw.qweather_key else 'NOT SET'}...")
print(f"qweather_host: {gw.qweather_host}")

print("\n=== 测试天气查询 ===")
result = gw.invoke('get_weather', {'city': '上海'})
print(f"OK: {result.ok}")
print(f"Text: {result.text}")
print(f"Provider: {result.raw.get('provider') if result.raw else 'unknown'}")
print(f"Error: {result.error}")
