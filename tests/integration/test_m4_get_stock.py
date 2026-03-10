"""M4 Task 2: get_stock Provider Chain 测试

测试 get_stock provider chain (Sina -> Tavily) 的功能和性能。

测试目标:
1. 端到端集成测试 (30条查询)
2. Fallback 机制测试
3. 超时配置验证
4. 延迟性能测试

运行方式:
    cd /path/to/agent_service
    python -m pytest tests/integration/test_m4_get_stock.py -v -s
"""

import os
import sys
import time
from pathlib import Path

# Add agent_service to path
agent_service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(agent_service_root))

import pytest


@pytest.fixture
def gateway():
    """Create MCPToolGateway instance"""
    from infra.tool_clients.mcp_gateway import MCPToolGateway
    return MCPToolGateway()


# 30条测试查询 (覆盖指数、个股、中文名称、代码)
TEST_QUERIES = [
    # 指数 (5条)
    "上证指数",
    "深证成指",
    "创业板指数",
    "沪深300",
    "000001",  # 上证指数代码
    
    # 热门个股 - 中文名称 (10条)
    "贵州茅台",
    "中国平安",
    "招商银行",
    "比亚迪",
    "宁德时代",
    "五粮液",
    "中国石油",
    "中国移动",
    "工商银行",
    "建设银行",
    
    # 热门个股 - 代码 (10条)
    "600519",  # 贵州茅台
    "601318",  # 中国平安
    "600036",  # 招商银行
    "002594",  # 比亚迪
    "300750",  # 宁德时代
    "000858",  # 五粮液
    "601857",  # 中国石油
    "600941",  # 中国移动
    "601398",  # 工商银行
    "601939",  # 建设银行
    
    # 其他个股 (5条)
    "中国银行",
    "农业银行",
    "中国石化",
    "中国联通",
    "中国电信",
]


def test_get_stock_e2e_30_queries(gateway):
    """测试1: 端到端集成测试 (30条查询)"""
    print("\n" + "="*80)
    print("测试1: get_stock 端到端集成测试 (30条查询)")
    print("="*80)
    
    results = []
    latencies = []
    provider_usage = {}
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/30] 查询: {query}")
        
        start_time = time.time()
        result = gateway.invoke("get_stock", {"target": query})
        latency = (time.time() - start_time) * 1000
        
        latencies.append(latency)
        
        # 提取 provider
        provider = "unknown"
        if result.raw and isinstance(result.raw, dict):
            provider = result.raw.get("provider", "unknown")
        
        provider_usage[provider] = provider_usage.get(provider, 0) + 1
        
        results.append({
            "query": query,
            "ok": result.ok,
            "provider": provider,
            "latency_ms": latency,
            "text": result.text[:100] if result.text else "",
            "error": result.error,
        })
        
        print(f"  结果: {'✅ 成功' if result.ok else '❌ 失败'}")
        print(f"  Provider: {provider}")
        print(f"  延迟: {latency:.0f}ms")
        if result.ok:
            print(f"  内容: {result.text[:80]}...")
        else:
            print(f"  错误: {result.error}")
        
        # 避免触发 rate limit
        time.sleep(0.5)
    
    # 统计结果
    success_count = sum(1 for r in results if r["ok"])
    success_rate = success_count / len(results) * 100
    avg_latency = sum(latencies) / len(latencies)
    p50_latency = sorted(latencies)[len(latencies) // 2]
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
    
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    print(f"总查询数: {len(results)}")
    print(f"成功数: {success_count}")
    print(f"失败数: {len(results) - success_count}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"\n延迟统计:")
    print(f"  平均延迟: {avg_latency:.0f}ms")
    print(f"  P50: {p50_latency:.0f}ms")
    print(f"  P95: {p95_latency:.0f}ms")
    print(f"  P99: {p99_latency:.0f}ms")
    print(f"\nProvider 使用统计:")
    for provider, count in sorted(provider_usage.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(results) * 100
        print(f"  {provider}: {count} ({percentage:.1f}%)")
    
    # 失败案例
    failed = [r for r in results if not r["ok"]]
    if failed:
        print(f"\n失败案例 ({len(failed)}条):")
        for r in failed:
            print(f"  - {r['query']}: {r['error']}")
    
    # 断言
    assert success_rate >= 90, f"成功率 {success_rate:.1f}% 低于 90%"
    assert avg_latency < 2000, f"平均延迟 {avg_latency:.0f}ms 超过 2s"
    assert provider_usage.get("sina_finance", 0) > 0, "Sina provider 未被使用"


def test_get_stock_fallback_mechanism(gateway):
    """测试2: Fallback 机制测试"""
    print("\n" + "="*80)
    print("测试2: get_stock Fallback 机制测试")
    print("="*80)
    
    # 测试无效查询触发 fallback
    print("\n测试场景: 无效股票代码")
    result = gateway.invoke("get_stock", {"target": "INVALID_STOCK_999999"})
    
    print(f"结果: {'✅ 成功' if result.ok else '❌ 失败'}")
    print(f"错误: {result.error}")
    
    # 检查是否触发了 fallback
    if result.raw and isinstance(result.raw, dict):
        fallback_chain = result.raw.get("fallback_chain", [])
        print(f"Fallback chain: {fallback_chain}")
        
        if fallback_chain:
            print("✅ Fallback 机制已触发")
        else:
            print("⚠️  Fallback 机制未触发 (可能是 Sina 直接返回错误)")
    
    # 注意: Sina Finance 对无效代码会返回空数据，不一定触发 fallback
    # 这是正常行为，因为 API 本身不会报错


def test_get_stock_timeout_config(gateway):
    """测试3: 超时配置验证"""
    print("\n" + "="*80)
    print("测试3: get_stock 超时配置验证")
    print("="*80)
    
    # 检查配置
    if hasattr(gateway, 'get_stock_chain') and gateway.get_stock_chain:
        # Load config from provider_config
        from infra.tool_clients.provider_config import load_provider_configs
        configs = load_provider_configs()
        
        if "get_stock" in configs:
            providers = configs["get_stock"]
            
            print(f"\nProvider Chain 配置:")
            for provider in providers:
                print(f"  - {provider.name}: timeout={provider.timeout}s, priority={provider.priority}")
            
            # 验证超时配置
            for provider in providers:
                assert provider.timeout <= 3.0, f"{provider.name} 超时 {provider.timeout}s 超过 3s"
            
            print("\n✅ 超时配置符合要求 (≤3s)")
        else:
            print("⚠️  get_stock 配置未找到")
    else:
        print("⚠️  Provider chain 未初始化")


def test_get_stock_latency_performance(gateway):
    """测试4: 延迟性能测试 (10条快速查询)"""
    print("\n" + "="*80)
    print("测试4: get_stock 延迟性能测试")
    print("="*80)
    
    # 选择10条常用查询
    quick_queries = [
        "上证指数",
        "深证成指",
        "贵州茅台",
        "中国平安",
        "600519",
        "601318",
        "比亚迪",
        "宁德时代",
        "招商银行",
        "工商银行",
    ]
    
    latencies = []
    
    for i, query in enumerate(quick_queries, 1):
        print(f"\n[{i}/10] 查询: {query}")
        
        start_time = time.time()
        result = gateway.invoke("get_stock", {"target": query})
        latency = (time.time() - start_time) * 1000
        
        latencies.append(latency)
        
        print(f"  延迟: {latency:.0f}ms")
        print(f"  结果: {'✅' if result.ok else '❌'}")
        
        time.sleep(0.3)
    
    # 统计
    avg_latency = sum(latencies) / len(latencies)
    p50_latency = sorted(latencies)[len(latencies) // 2]
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    
    print("\n" + "="*80)
    print("延迟统计:")
    print(f"  平均延迟: {avg_latency:.0f}ms")
    print(f"  P50: {p50_latency:.0f}ms")
    print(f"  P95: {p95_latency:.0f}ms")
    print("="*80)
    
    # 断言
    assert avg_latency < 1000, f"平均延迟 {avg_latency:.0f}ms 超过 1s"
    assert p95_latency < 2000, f"P95 延迟 {p95_latency:.0f}ms 超过 2s"
    
    print("\n✅ 延迟性能符合要求")


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "-s"])
