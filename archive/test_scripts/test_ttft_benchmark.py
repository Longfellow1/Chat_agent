"""TTFT (Time To First Token) Benchmark Test for qwen3.5-9b-mlx"""

import sys
import os
import time
from statistics import mean, median

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent_service'))

from infra.llm_clients.lm_studio_client import LMStudioClient


# Test queries (20 queries covering different scenarios)
TEST_QUERIES = [
    "你好",
    "今天天气怎么样",
    "上海有什么好玩的地方",
    "帮我查一下贵州茅台的股价",
    "附近有什么餐厅",
    "北京到上海怎么走",
    "明天会下雨吗",
    "推荐一个周末旅游的地方",
    "最近有什么新闻",
    "特斯拉股票涨了吗",
    "杭州西湖附近有什么酒店",
    "深圳有哪些充电桩",
    "成都的火锅店推荐",
    "广州天气预报",
    "苹果公司最新消息",
    "南京有什么景点",
    "武汉的樱花什么时候开",
    "重庆的轻轨怎么坐",
    "西安的兵马俑门票多少钱",
    "青岛的海鲜哪里好吃",
]


def measure_ttft(client: LMStudioClient, query: str, system_prompt: str = "你是一个助手") -> float:
    """Measure TTFT for a single query."""
    start = time.time()
    try:
        result = client.generate(query, system_prompt)
        ttft = time.time() - start
        return ttft
    except Exception as e:
        print(f"Error: {e}")
        return -1.0


def run_benchmark():
    """Run TTFT benchmark test."""
    print("=== TTFT Benchmark Test ===")
    print(f"Model: qwen3.5-9b-mlx")
    print(f"Test queries: {len(TEST_QUERIES)}")
    print()
    
    client = LMStudioClient()
    
    latencies = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] Testing: {query[:30]}...")
        ttft = measure_ttft(client, query)
        
        if ttft > 0:
            latencies.append(ttft)
            print(f"  TTFT: {ttft:.3f}s")
        else:
            print(f"  FAILED")
        print()
    
    # Calculate statistics
    if latencies:
        p50 = median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        avg = mean(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        
        print("=== Results ===")
        print(f"Total queries: {len(TEST_QUERIES)}")
        print(f"Successful: {len(latencies)}")
        print(f"Failed: {len(TEST_QUERIES) - len(latencies)}")
        print()
        print(f"P50 (Median): {p50:.3f}s")
        print(f"P95: {p95:.3f}s")
        print(f"Average: {avg:.3f}s")
        print(f"Min: {min_lat:.3f}s")
        print(f"Max: {max_lat:.3f}s")
        
        return {
            "model": "qwen3.5-9b-mlx",
            "total_queries": len(TEST_QUERIES),
            "successful": len(latencies),
            "failed": len(TEST_QUERIES) - len(latencies),
            "p50": p50,
            "p95": p95,
            "average": avg,
            "min": min_lat,
            "max": max_lat,
        }
    else:
        print("All queries failed!")
        return None


if __name__ == "__main__":
    result = run_benchmark()
    
    if result:
        print("\n=== Summary ===")
        print(f"Model: {result['model']}")
        print(f"P50: {result['p50']:.3f}s")
        print(f"P95: {result['p95']:.3f}s")
        print(f"Success rate: {result['successful']}/{result['total_queries']} ({result['successful']/result['total_queries']*100:.1f}%)")
