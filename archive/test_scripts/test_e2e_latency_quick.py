"""Quick E2E latency test - 5 queries"""

import sys
import os
import time
from pathlib import Path

# Load env
env_file = Path(__file__).parent / '.env.agent'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent_service'))

from app.orchestrator.chat_flow import ChatFlow

# 5 queries covering different tools
QUERIES = [
    "上海今天天气怎么样",  # get_weather
    "附近有什么停车场",  # find_nearby
    "贵州茅台股价",  # get_stock
    "最近有什么科技新闻",  # get_news
    "北京有什么好玩的",  # web_search
]

def test_e2e_latency():
    """Test end-to-end latency for 5 queries."""
    print("=== E2E Latency Test (5 queries) ===\n")
    
    flow = ChatFlow()
    latencies = []
    
    for i, query in enumerate(QUERIES, 1):
        print(f"[{i}/5] {query}")
        
        start = time.time()
        try:
            result = flow.run(query)
            elapsed = time.time() - start
            latencies.append(elapsed)
            print(f"  → {elapsed:.2f}s")
            print(f"  Response: {result[:80]}...\n")
        except Exception as e:
            print(f"  → ERROR: {e}\n")
    
    if latencies:
        avg = sum(latencies) / len(latencies)
        p50 = sorted(latencies)[len(latencies) // 2]
        
        print("=== Results ===")
        print(f"Queries: {len(latencies)}/5")
        print(f"P50: {p50:.2f}s")
        print(f"Average: {avg:.2f}s")
        print(f"Range: {min(latencies):.2f}s - {max(latencies):.2f}s")
        
        if p50 > 2.0:
            print(f"\n⚠️  WARNING: P50 {p50:.2f}s exceeds 2s target for voice")
        else:
            print(f"\n✅ P50 {p50:.2f}s within 2s target")

if __name__ == "__main__":
    test_e2e_latency()
