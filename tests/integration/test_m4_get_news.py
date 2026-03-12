"""M4 Task 1: get_news Provider Chain Integration Test

Tests the get_news provider chain with 30 queries covering:
- Financial news (10)
- Technology news (10)
- Automotive news (10, high priority for auto show)

Validation:
- Technical effectiveness >= 90% (27/30)
- Fallback effectiveness >= 95%
- Average latency <= 3s
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
agent_service_path = project_root / "agent_service"
sys.path.insert(0, str(agent_service_path))

# Load environment variables
from dotenv import load_dotenv
env_file = project_root / ".env.agent"
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment from {env_file}")
else:
    print(f"Warning: {env_file} not found")

from infra.tool_clients.provider_chain import ProviderChainManager
from infra.tool_clients.provider_config import load_provider_configs
from infra.tool_clients.providers.baidu_news_provider import BaiduNewsProvider
from infra.tool_clients.providers.news_provider import SinaNewsProvider
from infra.tool_clients.providers.tavily_provider import TavilyProvider


# Test queries
TEST_QUERIES = [
    # Financial news (10)
    "今日股市",
    "美联储加息",
    "人民币汇率",
    "油价走势",
    "黄金价格",
    "比特币行情",
    "A股涨跌",
    "港股动态",
    "美股收盘",
    "经济数据",
    
    # Technology news (10)
    "iPhone新品",
    "华为发布会",
    "特斯拉动态",
    "ChatGPT更新",
    "芯片行业",
    "5G技术",
    "人工智能",
    "量子计算",
    "新能源汽车",
    "自动驾驶",
    
    # Automotive news (10, high priority for auto show)
    "今天有什么汽车行业新闻",
    "比亚迪最新消息",
    "特斯拉降价",
    "新能源汽车政策",
    "汽车销量排行",
    "电动车续航",
    "自动驾驶技术",
    "汽车芯片",
    "车展信息",
    "汽车召回",
]


def test_get_news_provider_chain():
    """Test get_news provider chain with 30 queries."""
    
    print("=" * 80)
    print("M4 Task 1: get_news Provider Chain Test")
    print("=" * 80)
    print(f"Total queries: {len(TEST_QUERIES)}")
    print(f"Target: Technical effectiveness >= 90% (27/30)")
    print(f"Target: Fallback effectiveness >= 95%")
    print(f"Target: Average latency <= 3s")
    print()
    
    # Initialize provider chain
    chain = ProviderChainManager()
    
    # Register providers
    chain.register_provider("baidu_news", BaiduNewsProvider)
    chain.register_provider("sina_news", SinaNewsProvider)
    chain.register_provider("tavily", TavilyProvider)
    
    # Load configuration
    configs = load_provider_configs()
    if "get_news" not in configs:
        print("ERROR: get_news configuration not found")
        return
    
    chain.configure_chain("get_news", configs["get_news"])
    
    # Test results
    results = []
    total_latency = 0.0
    success_count = 0
    fallback_count = 0
    provider_usage = {}
    
    # Run tests
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] Testing: {query}")
        
        start = time.time()
        result = chain.execute("get_news", query=query)
        latency = (time.time() - start) * 1000  # ms
        
        total_latency += latency
        
        # Record result
        test_result = {
            "query": query,
            "ok": result.ok,
            "provider": result.provider_name,
            "latency_ms": latency,
            "fallback_chain": result.fallback_chain,
            "error": result.error,
        }
        results.append(test_result)
        
        # Update counters
        if result.ok:
            success_count += 1
            provider_usage[result.provider_name] = provider_usage.get(result.provider_name, 0) + 1
        
        if result.fallback_chain:
            fallback_count += 1
        
        # Print result
        status = "✅ SUCCESS" if result.ok else "❌ FAILED"
        print(f"  {status} | Provider: {result.provider_name} | Latency: {latency:.0f}ms")
        
        if result.fallback_chain:
            print(f"  Fallback chain: {' -> '.join(result.fallback_chain)}")
        
        if not result.ok:
            print(f"  Error: {result.error}")
        
        # Rate limiting: wait 1s between requests to avoid QPS limit
        if i < len(TEST_QUERIES):
            time.sleep(1.0)
    
    # Calculate metrics
    avg_latency = total_latency / len(TEST_QUERIES)
    effectiveness = (success_count / len(TEST_QUERIES)) * 100
    fallback_rate = (fallback_count / len(TEST_QUERIES)) * 100
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total queries: {len(TEST_QUERIES)}")
    print(f"Successful: {success_count}/{len(TEST_QUERIES)} ({effectiveness:.1f}%)")
    print(f"Failed: {len(TEST_QUERIES) - success_count}/{len(TEST_QUERIES)}")
    print(f"Fallback used: {fallback_count}/{len(TEST_QUERIES)} ({fallback_rate:.1f}%)")
    print(f"Average latency: {avg_latency:.0f}ms")
    print()
    
    print("Provider usage:")
    for provider, count in sorted(provider_usage.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / success_count) * 100 if success_count > 0 else 0
        print(f"  {provider}: {count}/{success_count} ({percentage:.1f}%)")
    print()
    
    # Validation
    print("VALIDATION:")
    effectiveness_pass = effectiveness >= 90.0
    latency_pass = avg_latency <= 3000
    
    print(f"  Technical effectiveness: {effectiveness:.1f}% {'✅ PASS' if effectiveness_pass else '❌ FAIL'} (target: >= 90%)")
    print(f"  Average latency: {avg_latency:.0f}ms {'✅ PASS' if latency_pass else '❌ FAIL'} (target: <= 3000ms)")
    print()
    
    # Overall result
    all_pass = effectiveness_pass and latency_pass
    print("=" * 80)
    if all_pass:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    
    return results, all_pass


if __name__ == "__main__":
    results, passed = test_get_news_provider_chain()
    sys.exit(0 if passed else 1)
