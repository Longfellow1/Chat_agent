"""Test Bing MCP with 30 web search queries."""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent_service"))

from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.providers.bing_mcp_provider import BingMCPProvider

# Read queries
queries = []
with open('web_search_30_queries.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    queries = list(reader)

print(f"Testing {len(queries)} queries with Bing MCP")
print("=" * 80)

# Initialize provider
config = ProviderConfig(
    name="bing_mcp",
    priority=1,
    timeout=10.0,
)
provider = BingMCPProvider(config)

# Test queries
results = []
success_count = 0
fail_count = 0

for i, q in enumerate(queries, 1):
    query = q['query']
    print(f"\n[{i}/{len(queries)}] {query}")
    print("-" * 80)
    
    start_time = time.time()
    result = provider.execute(query=query)
    elapsed = time.time() - start_time
    
    if result.ok:
        success_count += 1
        status = "✓"
        print(f"{status} 成功 ({elapsed:.2f}s)")
        print(f"结果: {result.data.text[:200]}...")
    else:
        fail_count += 1
        status = "✗"
        print(f"{status} 失败: {result.error}")
    
    results.append({
        'query': query,
        'status': status,
        'ok': result.ok,
        'error': result.error if not result.ok else '',
        'elapsed': f"{elapsed:.2f}s",
        'result_preview': result.data.text[:100] if result.ok else ''
    })
    
    # Rate limiting
    time.sleep(2)

# Summary
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print(f"总查询数: {len(queries)}")
print(f"成功: {success_count} ({success_count/len(queries)*100:.1f}%)")
print(f"失败: {fail_count} ({fail_count/len(queries)*100:.1f}%)")

# Save results
with open('bing_mcp_test_results.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['query', 'status', 'ok', 'error', 'elapsed', 'result_preview'])
    writer.writeheader()
    writer.writerows(results)

print(f"\n结果已保存到: bing_mcp_test_results.csv")
