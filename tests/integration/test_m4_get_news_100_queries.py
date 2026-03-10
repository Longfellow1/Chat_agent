"""M4 get_news 100条压测 - 获取真实 P95/P99 延迟

运行方式:
    cd /path/to/agent_service
    python -m pytest tests/integration/test_m4_get_news_100_queries.py -v -s
"""

import os
import sys
import time
from pathlib import Path

# Load .env.agent
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env.agent"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")

# Add agent_service to path
agent_service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(agent_service_root))

import pytest


@pytest.fixture
def gateway():
    """Create MCPToolGateway instance"""
    from infra.tool_clients.mcp_gateway import MCPToolGateway
    return MCPToolGateway()


# 100条测试查询 (覆盖多种新闻类型)
TEST_QUERIES = [
    # 汽车新闻 (20条)
    "比亚迪新能源汽车", "特斯拉最新动态", "蔚来汽车", "理想汽车", "小鹏汽车",
    "奔驰新车发布", "宝马电动车", "奥迪最新消息", "丰田混动", "本田新车",
    "大众ID系列", "吉利汽车", "长城汽车", "长安汽车", "广汽埃安",
    "问界汽车", "极氪汽车", "智己汽车", "飞凡汽车", "岚图汽车",
    
    # 科技新闻 (20条)
    "人工智能", "ChatGPT", "华为鸿蒙", "苹果新品", "小米手机",
    "OPPO新机", "vivo手机", "三星Galaxy", "芯片技术", "5G网络",
    "量子计算", "云计算", "大数据", "物联网", "区块链",
    "元宇宙", "虚拟现实", "增强现实", "自动驾驶", "机器人",
    
    # 财经新闻 (20条)
    "股市行情", "A股走势", "美股动态", "港股消息", "基金投资",
    "房地产市场", "黄金价格", "原油价格", "人民币汇率", "美元指数",
    "经济政策", "货币政策", "财政政策", "通货膨胀", "GDP增长",
    "就业数据", "消费数据", "进出口", "外汇储备", "利率调整",
    
    # 社会新闻 (20条)
    "教育改革", "医疗健康", "养老保险", "住房公积金", "个税政策",
    "环境保护", "气候变化", "新能源", "碳中和", "碳达峰",
    "食品安全", "药品监管", "疫苗接种", "公共卫生", "社会保障",
    "就业创业", "收入分配", "扶贫攻坚", "乡村振兴", "城市建设",
    
    # 国际新闻 (20条)
    "中美关系", "中欧关系", "俄乌局势", "中东局势", "朝鲜半岛",
    "日本政治", "韩国经济", "东南亚", "印度发展", "巴西经济",
    "欧盟政策", "英国脱欧", "德国大选", "法国改革", "意大利经济",
    "联合国", "世界银行", "国际货币基金", "世贸组织", "G20峰会",
]


def test_get_news_100_queries_stress_test(gateway):
    """100条查询压测 - 获取真实 P95/P99 延迟"""
    print("\n" + "="*80)
    print("get_news 100条压测")
    print("="*80)
    
    results = []
    latencies = []
    provider_usage = {}
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\r[{i}/100] 查询: {query[:20]}...", end="", flush=True)
        
        start_time = time.time()
        result = gateway.invoke("get_news", {"topic": query})
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
            "error": result.error,
        })
        
        # 避免触发 rate limit
        time.sleep(0.3)
    
    print("\n")
    
    # 统计结果
    success_count = sum(1 for r in results if r["ok"])
    success_rate = success_count / len(results) * 100
    
    # 延迟统计
    sorted_latencies = sorted(latencies)
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    p50_latency = sorted_latencies[len(sorted_latencies) // 2]
    p90_latency = sorted_latencies[int(len(sorted_latencies) * 0.90)]
    p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]
    
    print("="*80)
    print("测试结果汇总")
    print("="*80)
    print(f"总查询数: {len(results)}")
    print(f"成功数: {success_count}")
    print(f"失败数: {len(results) - success_count}")
    print(f"成功率: {success_rate:.1f}%")
    
    print(f"\n延迟统计:")
    print(f"  最小延迟: {min_latency:.0f}ms")
    print(f"  平均延迟: {avg_latency:.0f}ms")
    print(f"  最大延迟: {max_latency:.0f}ms")
    print(f"  P50: {p50_latency:.0f}ms")
    print(f"  P90: {p90_latency:.0f}ms")
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
        for r in failed[:10]:  # 只显示前10条
            print(f"  - {r['query']}: {r['error']}")
        if len(failed) > 10:
            print(f"  ... 还有 {len(failed) - 10} 条失败")
    
    # 延迟分布
    print(f"\n延迟分布:")
    buckets = {
        "< 300ms": sum(1 for l in latencies if l < 300),
        "300-500ms": sum(1 for l in latencies if 300 <= l < 500),
        "500-1000ms": sum(1 for l in latencies if 500 <= l < 1000),
        "1000-2000ms": sum(1 for l in latencies if 1000 <= l < 2000),
        ">= 2000ms": sum(1 for l in latencies if l >= 2000),
    }
    for bucket, count in buckets.items():
        percentage = count / len(latencies) * 100
        print(f"  {bucket}: {count} ({percentage:.1f}%)")
    
    # 断言
    assert success_rate >= 90, f"成功率 {success_rate:.1f}% 低于 90%"
    assert p95_latency < 2000, f"P95 延迟 {p95_latency:.0f}ms 超过 2s"
    assert provider_usage.get("baidu_news", 0) > 0, "Baidu provider 未被使用"
    
    print("\n✅ 压测通过")


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "-s"])
