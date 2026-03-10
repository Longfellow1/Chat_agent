"""Test failed queries with lower threshold."""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'agent_service'))

from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.providers.bing_mcp_provider import BingMCPProvider

# Failed queries from previous test
failed_queries = [
    "华为Mate 60 Pro参数",
    "小米14 Ultra拍照样张",
    "成都大熊猫基地开放时间",
    "繁花电视剧豆瓣评分",
    "三体动画第二季上映时间",
    "周杰伦演唱会2024",
    "泰勒斯威夫特中国巡演",
    "日本旅游签证办理流程",
    "泰国落地签最新政策",
    "欧洲申根签证材料",
    "糖尿病最新治疗方法",
    "新冠疫苗接种指南",
    "孕期营养补充建议",
]

config = ProviderConfig(name='bing_mcp', priority=1, timeout=10.0)
provider = BingMCPProvider(config)

print(f"测试 {len(failed_queries)} 个之前失败的查询")
print("=" * 80)

success = 0
fail = 0

for i, query in enumerate(failed_queries, 1):
    print(f"\n[{i}/{len(failed_queries)}] {query}")
    print("-" * 80)
    
    result = provider.execute(query=query)
    
    if result.ok:
        success += 1
        print(f"✓ 成功")
        print(result.data.text[:200])
    else:
        fail += 1
        print(f"✗ 失败: {result.error}")

print("\n" + "=" * 80)
print(f"成功: {success}/{len(failed_queries)} ({success/len(failed_queries)*100:.1f}%)")
print(f"失败: {fail}/{len(failed_queries)} ({fail/len(failed_queries)*100:.1f}%)")
