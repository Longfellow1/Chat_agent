#!/usr/bin/env python3
"""测试 Provider Chain 的健壮性和 fallback 机制"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

# 设置环境变量
os.environ["BAIDU_QIANFAN_API_KEY"] = "REDACTED"

from infra.tool_clients.provider_chain import ProviderChainManager
from infra.tool_clients.provider_config import load_provider_configs
from infra.tool_clients.providers import (
    BaiduWebSearchProvider,
    BingMCPProvider,
    TavilyProvider,
)

print("="*80)
print("Provider Chain 健壮性测试")
print("="*80)

# 创建 provider chain manager
manager = ProviderChainManager()

# 注册 providers
manager.register_provider("baidu_web_search", BaiduWebSearchProvider)
manager.register_provider("bing_mcp", BingMCPProvider)
manager.register_provider("tavily", TavilyProvider)

# 加载配置
configs = load_provider_configs()
web_search_config = configs.get("web_search", [])

print(f"\nProvider 优先级配置:")
for config in sorted(web_search_config, key=lambda x: x.priority):
    print(f"  {config.priority}. {config.name} (timeout={config.timeout}s, enabled={config.enabled})")

# 配置 chain
manager.configure_chain("web_search", web_search_config)

# 测试查询
test_queries = [
    "特斯拉Model 3最新价格",
    "比亚迪汉EV续航测试",
    "iPhone 15 Pro评测",
]

print(f"\n{'='*80}")
print("执行测试查询")
print(f"{'='*80}\n")

for i, query in enumerate(test_queries, 1):
    print(f"[{i}/{len(test_queries)}] {query}")
    
    result = manager.execute("web_search", query=query)
    
    if result.ok:
        print(f"  ✅ 成功")
        print(f"  Provider: {result.provider_name}")
        print(f"  延迟: {result.latency_ms:.0f}ms")
        
        if result.fallback_chain:
            print(f"  Fallback 链: {' -> '.join(result.fallback_chain)}")
        
        # 显示结果数量
        if result.data and result.data.raw:
            result_count = len(result.data.raw.get("results", []))
            print(f"  结果数: {result_count}")
            
            # 显示第一条结果
            results = result.data.raw.get("results", [])
            if results:
                first = results[0]
                print(f"  首条: {first.get('title', '')[:50]}...")
    else:
        print(f"  ❌ 失败: {result.error}")
        if result.fallback_chain:
            print(f"  Fallback 链: {' -> '.join(result.fallback_chain)}")
    
    print()

# 显示指标
print(f"{'='*80}")
print("Provider 指标")
print(f"{'='*80}\n")

metrics = manager.get_metrics("web_search")
for provider_name, metric in metrics.items():
    print(f"{provider_name}:")
    print(f"  总调用: {metric.total_calls}")
    print(f"  成功: {metric.success_calls}")
    print(f"  失败: {metric.failed_calls}")
    print(f"  成功率: {metric.success_rate*100:.1f}%")
    if metric.success_calls > 0:
        print(f"  平均延迟: {metric.avg_latency_ms:.0f}ms")
    print(f"  Fallback: {metric.fallback_count}")
    print()

print(f"{'='*80}")
print("测试完成")
print(f"{'='*80}")
