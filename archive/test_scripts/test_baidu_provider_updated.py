#!/usr/bin/env python3
"""Test updated BaiduAISearchProvider from baidu_providers.py"""

import os
import sys

# Add agent_service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent_service"))

from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.providers.baidu_providers import BaiduAISearchProvider

# Set API key
os.environ["BAIDU_QIANFAN_API_KEY"] = "REDACTED"

print("="*80)
print("测试更新后的 BaiduAISearchProvider")
print("="*80)

# Create provider
config = ProviderConfig(
    name="baidu_ai_search",
    priority=2,
    timeout=10.0,
    enabled=True,
)

provider = BaiduAISearchProvider(config)

# Test health check
print(f"\n健康检查: {provider.health_check()}")

# Test search
query = "今天有哪些财经新闻"
print(f"\n查询: {query}")
print(f"{'='*80}\n")

result = provider.execute(query=query)

print(f"执行结果:")
print(f"  ok: {result.ok}")
print(f"  provider: {result.provider_name}")
print(f"  result_type: {result.result_type}")
print(f"  error: {result.error}")

if result.ok and result.data:
    print(f"\n内容:")
    print(f"{result.data.text}")
    print(f"\nRaw data keys: {list(result.data.raw.keys())}")
else:
    print(f"\n失败原因: {result.error}")
    if "rate_limit" in str(result.error):
        print(f"\n✅ 速率限制检测正常 - 说明端点和认证都正确")

print(f"\n{'='*80}")
print("测试完成")
print(f"{'='*80}")
