#!/usr/bin/env python3
"""Debug Bing MCP - 直接调用provider看原始返回"""

import sys
import os
sys.path.insert(0, ".")
os.chdir("/Users/Harland/Documents/evaluation")

from agent_service.infra.tool_clients.providers.bing_mcp_provider import BingMCPProvider
from agent_service.infra.tool_clients.provider_base import ProviderConfig

# 创建provider
config = ProviderConfig(
    name="bing_mcp",
    timeout=10,
    max_retries=1,
)

provider = BingMCPProvider(config)

# 测试3条"基于现有搜索结果未能找到相关信息"的query
queries = [
    "帮我搜一下去西藏旅游需要注意什么",
    "帮我查下北京有什么好玩的地方推荐几个",
    "帮我查下二手车价格怎么样",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    result = provider.execute(query=query)
    
    print(f"OK: {result.ok}")
    print(f"Error: {result.error}")
    
    if result.data:
        print(f"Text: {result.data.text[:300]}")
        print(f"Results count: {len(result.data.raw.get('results', []))}")
        if result.data.raw.get('results'):
            print(f"First result: {result.data.raw['results'][0]}")
    else:
        print("No data returned")
