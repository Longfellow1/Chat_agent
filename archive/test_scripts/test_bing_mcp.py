"""Test Bing MCP provider."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent_service"))

from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.providers.bing_mcp_provider import BingMCPProvider

print("=" * 60)
print("测试 Bing MCP Provider")
print("=" * 60)

config = ProviderConfig(
    name="bing_mcp",
    priority=1,
    timeout=5.0,
)

provider = BingMCPProvider(config)

# Health check
print("\n1. Health Check...")
healthy = provider.health_check()
print(f"{'✓' if healthy else '✗'} Health: {healthy}")

# Test search
print("\n2. 测试搜索: '特斯拉 Model 3 价格'")
print("-" * 60)

result = provider.execute(query="特斯拉 Model 3 价格")

if result.ok:
    print(f"✓ 成功")
    print(f"Provider: {result.provider_name}")
    print(f"Result Type: {result.result_type.value}")
    print(f"Latency: {result.latency_ms:.2f}ms")
    print(f"\n结果:\n{result.data.text[:500]}")
else:
    print(f"✗ 失败: {result.error}")

print("\n" + "=" * 60)
