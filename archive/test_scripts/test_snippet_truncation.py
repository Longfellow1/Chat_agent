#!/usr/bin/env python3
"""测试调整后的 snippet 截断策略"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

os.environ["BAIDU_QIANFAN_API_KEY"] = "REDACTED"

from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.providers.baidu_web_search_provider import BaiduWebSearchProvider

# 创建 provider
config = ProviderConfig(
    name="baidu_web_search",
    priority=1,
    timeout=10.0,
)

provider = BaiduWebSearchProvider(config)

print(f"配置的 snippet_chars: {provider.snippet_chars}")
print(f"{'='*80}\n")

# 测试查询
query = "比亚迪汉EV续航测试"
print(f"查询: {query}\n")

result = provider.execute(query=query)

if result.ok:
    print("✅ 成功\n")
    print("返回的文本内容:")
    print(result.data.text)
    print(f"\n{'='*80}")
    print("原始结果详情:")
    for i, r in enumerate(result.data.raw["results"], 1):
        print(f"\n{i}. {r['title']}")
        print(f"   URL: {r['url']}")
        print(f"   Snippet 长度: {len(r['snippet'])} 字符")
        print(f"   Snippet: {r['snippet'][:150]}...")
else:
    print(f"❌ 失败: {result.error}")
