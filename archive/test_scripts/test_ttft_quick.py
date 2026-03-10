"""Quick TTFT Test - 5 queries only"""

import sys
import os
import time
from statistics import mean, median

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent_service'))

from infra.llm_clients.lm_studio_client import LMStudioClient


TEST_QUERIES = [
    "你好",
    "今天天气怎么样",
    "上海有什么好玩的地方",
    "附近有什么餐厅",
    "明天会下雨吗",
]


def measure_ttft(client: LMStudioClient, query: str) -> float:
    """Measure TTFT for a single query."""
    start = time.time()
    try:
        result = client.generate(query, "你是一个助手")
        ttft = time.time() - start
        return ttft
    except Exception as e:
        print(f"Error: {e}")
        return -1.0


def run_benchmark():
    """Run quick TTFT benchmark."""
    print("=== Quick TTFT Test (5 queries) ===")
    print(f"Model: qwen3.5-9b-mlx\n")
    
    client = LMStudioClient()
    latencies = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/5] {query}")
        ttft = measure_ttft(client, query)
        
        if ttft > 0:
            latencies.append(ttft)
            print(f"  → {ttft:.2f}s\n")
        else:
            print(f"  → FAILED\n")
    
    if latencies:
        p50 = median(latencies)
        avg = mean(latencies)
        
        print("=== Results ===")
        print(f"Successful: {len(latencies)}/5")
        print(f"P50: {p50:.2f}s")
        print(f"Average: {avg:.2f}s")
        print(f"Range: {min(latencies):.2f}s - {max(latencies):.2f}s")
        
        return {"p50": p50, "avg": avg, "success": len(latencies)}
    else:
        print("All queries failed!")
        return None


if __name__ == "__main__":
    run_benchmark()
