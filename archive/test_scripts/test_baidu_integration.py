"""Test Baidu integration (Baike + Search MCP)."""

import os
import sys

# Add agent_service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent_service"))

from domain.intents.encyclopedia_router import EncyclopediaRouter
from infra.tool_clients.mcp_gateway import MCPToolGateway


def test_encyclopedia_router():
    """Test encyclopedia router."""
    print("=" * 60)
    print("Testing Encyclopedia Router")
    print("=" * 60)
    
    router = EncyclopediaRouter()
    
    test_cases = [
        ("什么是电动汽车", "encyclopedia"),
        ("特斯拉 Model 3 价格", "web_search"),
        ("马斯克是谁", "encyclopedia"),
        ("比亚迪和特斯拉哪个好", "web_search"),
        ("锂电池原理", "encyclopedia"),
        ("上海电动车补贴政策", "web_search"),
    ]
    
    for query, expected in test_cases:
        result = router.route(query)
        status = "✓" if result == expected else "✗"
        print(f"{status} {query:30s} -> {result:15s} (expected: {expected})")
    
    print()


def test_baidu_baike():
    """Test Baidu Baike provider."""
    print("=" * 60)
    print("Testing Baidu Baike Provider")
    print("=" * 60)
    
    # Check if access key is set
    access_key = os.getenv("BAIDU_BCE_ACCESS_KEY", "").strip()
    if not access_key:
        print("⚠ BAIDU_BCE_ACCESS_KEY not set, skipping actual API test")
        print()
        return
    
    gateway = MCPToolGateway()
    
    test_queries = [
        "什么是电动汽车",
        "特斯拉公司介绍",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        try:
            result = gateway.invoke("encyclopedia", {"query": query})
            
            if result.ok:
                print(f"✓ Success")
                print(f"Provider: {result.raw.get('provider_name', 'unknown')}")
                print(f"Text: {result.text[:200]}...")
            else:
                print(f"✗ Failed: {result.error}")
        except Exception as e:
            print(f"✗ Exception: {e}")
    
    print()


def test_baidu_search_mcp():
    """Test Baidu Search MCP provider."""
    print("=" * 60)
    print("Testing Baidu Search MCP Provider")
    print("=" * 60)
    
    # Check if access key is set
    access_key = os.getenv("BAIDU_BCE_ACCESS_KEY", "").strip()
    if not access_key:
        print("⚠ BAIDU_BCE_ACCESS_KEY not set, skipping actual API test")
        print()
        return
    
    gateway = MCPToolGateway()
    
    test_queries = [
        "特斯拉 Model 3 价格",
        "比亚迪最新消息",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        try:
            result = gateway.invoke("web_search", {"query": query})
            
            if result.ok:
                print(f"✓ Success")
                print(f"Provider: {result.raw.get('provider_name', 'unknown')}")
                print(f"Text: {result.text[:300]}...")
            else:
                print(f"✗ Failed: {result.error}")
        except Exception as e:
            print(f"✗ Exception: {e}")
    
    print()


def test_provider_metrics():
    """Test provider metrics."""
    print("=" * 60)
    print("Provider Metrics")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    for tool_name in ["encyclopedia", "web_search"]:
        print(f"\n{tool_name}:")
        print("-" * 60)
        
        metrics = gateway.get_provider_metrics(tool_name)
        
        if not metrics:
            print("No metrics available")
            continue
        
        for provider_name, provider_metrics in metrics.items():
            print(f"\n  {provider_name}:")
            print(f"    Total calls: {provider_metrics['total_calls']}")
            print(f"    Success rate: {provider_metrics['success_rate']:.2%}")
            print(f"    Avg latency: {provider_metrics['avg_latency_ms']:.2f}ms")
            print(f"    Fallback count: {provider_metrics['fallback_count']}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Baidu Integration Test Suite")
    print("=" * 60 + "\n")
    
    # Test 1: Router
    test_encyclopedia_router()
    
    # Test 2: Baidu Baike
    test_baidu_baike()
    
    # Test 3: Baidu Search MCP
    test_baidu_search_mcp()
    
    # Test 4: Metrics
    test_provider_metrics()
    
    print("=" * 60)
    print("Test suite completed")
    print("=" * 60)
