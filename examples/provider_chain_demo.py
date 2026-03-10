"""Provider Chain demonstration script.

This script demonstrates the key features of the Provider Chain architecture:
1. Automatic fallback to backup providers
2. Metrics and monitoring
3. Runtime configuration updates
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_service'))

from infra.tool_clients.mcp_gateway import MCPToolGateway


def demo_basic_usage():
    """Demonstrate basic usage with automatic fallback."""
    print("=" * 60)
    print("Demo 1: Basic Usage with Automatic Fallback")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    # Call find_nearby
    print("\n调用 find_nearby: 上海 咖啡厅")
    result = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})
    
    if result.ok:
        print(f"\n✅ 成功!")
        print(f"Provider: {result.raw.get('provider_name')}")
        print(f"延迟: {result.raw.get('provider_latency_ms', 0):.2f}ms")
        
        if result.raw.get('fallback_chain'):
            print(f"降级链: {' -> '.join(result.raw['fallback_chain'])}")
        
        print(f"\n结果:\n{result.text[:200]}...")
    else:
        print(f"\n❌ 失败: {result.error}")
        if result.raw and result.raw.get('fallback_chain'):
            print(f"尝试过的Provider: {result.raw['fallback_chain']}")


def demo_metrics():
    """Demonstrate metrics and monitoring."""
    print("\n" + "=" * 60)
    print("Demo 2: Metrics and Monitoring")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    # Make multiple calls
    print("\n执行5次调用...")
    for i in range(5):
        gateway.invoke("find_nearby", {"keyword": "餐厅", "city": "北京"})
    
    # Get metrics
    print("\nProvider指标:")
    metrics = gateway.get_provider_metrics("find_nearby")
    
    for provider_name, stats in metrics.items():
        print(f"\n{provider_name}:")
        print(f"  总调用: {stats['total_calls']}")
        print(f"  成功: {stats['success_calls']}")
        print(f"  失败: {stats['failed_calls']}")
        print(f"  成功率: {stats['success_rate']:.2%}")
        print(f"  平均延迟: {stats['avg_latency_ms']:.2f}ms")
        print(f"  超时次数: {stats['timeout_count']}")
        print(f"  错误次数: {stats['error_count']}")
        print(f"  降级次数: {stats['fallback_count']}")


def demo_runtime_config():
    """Demonstrate runtime configuration updates."""
    print("\n" + "=" * 60)
    print("Demo 3: Runtime Configuration Updates")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    # Original call
    print("\n原始配置调用:")
    result1 = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})
    print(f"Provider: {result1.raw.get('provider_name') if result1.raw else 'unknown'}")
    
    # Disable primary provider
    print("\n禁用 amap_mcp...")
    gateway.update_provider_config("find_nearby", "amap_mcp", enabled=False)
    
    # Call again
    print("\n禁用后调用:")
    result2 = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})
    print(f"Provider: {result2.raw.get('provider_name') if result2.raw else 'unknown'}")
    
    if result2.raw and result2.raw.get('fallback_chain'):
        print(f"降级链: {result2.raw['fallback_chain']}")
    
    # Re-enable
    print("\n重新启用 amap_mcp...")
    gateway.update_provider_config("find_nearby", "amap_mcp", enabled=True)
    
    # Call again
    print("\n重新启用后调用:")
    result3 = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})
    print(f"Provider: {result3.raw.get('provider_name') if result3.raw else 'unknown'}")


def demo_web_search():
    """Demonstrate web search with provider chain."""
    print("\n" + "=" * 60)
    print("Demo 4: Web Search with Provider Chain")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    print("\n调用 web_search: Python 最新版本")
    result = gateway.invoke("web_search", {"query": "Python 最新版本"})
    
    if result.ok:
        print(f"\n✅ 成功!")
        print(f"Provider: {result.raw.get('provider_name')}")
        print(f"延迟: {result.raw.get('provider_latency_ms', 0):.2f}ms")
        print(f"\n结果:\n{result.text[:300]}...")
    else:
        print(f"\n❌ 失败: {result.error}")


def demo_fallback_scenario():
    """Demonstrate fallback scenario by simulating failures."""
    print("\n" + "=" * 60)
    print("Demo 5: Fallback Scenario Simulation")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    # Disable primary providers to force fallback
    print("\n模拟主Provider失败...")
    gateway.update_provider_config("find_nearby", "amap_mcp", enabled=False)
    gateway.update_provider_config("find_nearby", "amap_direct", enabled=False)
    
    print("\n调用 find_nearby (只有web_search_fallback和mock可用):")
    result = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})
    
    if result.ok:
        print(f"\n✅ 成功降级!")
        print(f"Provider: {result.raw.get('provider_name')}")
        
        if result.raw.get('fallback_chain'):
            print(f"\n降级链:")
            for step in result.raw['fallback_chain']:
                print(f"  ❌ {step}")
            print(f"  ✅ {result.raw.get('provider_name')}")
    else:
        print(f"\n❌ 所有Provider都失败: {result.error}")
    
    # Restore
    gateway.update_provider_config("find_nearby", "amap_mcp", enabled=True)
    gateway.update_provider_config("find_nearby", "amap_direct", enabled=True)


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("Provider Chain Architecture Demo")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_metrics()
        demo_runtime_config()
        demo_web_search()
        demo_fallback_scenario()
        
        print("\n" + "=" * 60)
        print("Demo完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
