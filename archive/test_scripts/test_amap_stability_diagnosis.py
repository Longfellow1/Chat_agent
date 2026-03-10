"""Diagnose Amap MCP stability issues"""

import sys
import os
import time

# Load environment variables from .env.agent
from pathlib import Path
env_file = Path(__file__).parent / '.env.agent'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent_service'))

from infra.tool_clients.amap_mcp_client import AmapMCPClient


def test_single_query(client: AmapMCPClient, keyword: str, city: str, attempt: int):
    """Test a single query and return detailed diagnostics."""
    print(f"\n[Attempt {attempt}] Testing: {keyword} @ {city}")
    
    start = time.time()
    try:
        result = client.find_nearby(keyword=keyword, city=city)
        elapsed = time.time() - start
        
        if result.ok:
            provider = result.raw.get("provider") if result.raw else "unknown"
            print(f"  ✅ SUCCESS ({elapsed:.2f}s) - Provider: {provider}")
            return {"success": True, "elapsed": elapsed, "provider": provider, "error": None}
        else:
            print(f"  ❌ FAILED ({elapsed:.2f}s) - Error: {result.error}")
            return {"success": False, "elapsed": elapsed, "provider": None, "error": result.error}
    
    except Exception as e:
        elapsed = time.time() - start
        print(f"  💥 EXCEPTION ({elapsed:.2f}s) - {type(e).__name__}: {e}")
        return {"success": False, "elapsed": elapsed, "provider": None, "error": str(e)}


def run_stability_test():
    """Run stability test with multiple queries."""
    print("=== Amap MCP Stability Diagnosis ===\n")
    
    # Test queries
    queries = [
        ("停车场", "上海"),
        ("餐厅", "北京"),
        ("充电桩", "深圳"),
        ("咖啡厅", "杭州"),
        ("加油站", "成都"),
        ("便利店", "武汉"),
        ("银行", "南京"),
        ("药店", "西安"),
        ("超市", "重庆"),
        ("酒店", "苏州"),
    ]
    
    client = AmapMCPClient()
    results = []
    
    # Run tests
    for i, (keyword, city) in enumerate(queries, 1):
        result = test_single_query(client, keyword, city, i)
        results.append(result)
        time.sleep(0.5)  # Small delay between queries
    
    # Analyze results
    print("\n=== Analysis ===")
    
    success_count = sum(1 for r in results if r["success"])
    amap_count = sum(1 for r in results if r.get("provider") == "amap_mcp")
    
    print(f"Total queries: {len(results)}")
    print(f"Successful: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"Amap MCP used: {amap_count} ({amap_count/len(results)*100:.1f}%)")
    
    # Error breakdown
    errors = {}
    for r in results:
        if not r["success"] and r["error"]:
            error_type = r["error"].split(":")[0] if ":" in r["error"] else r["error"]
            errors[error_type] = errors.get(error_type, 0) + 1
    
    if errors:
        print("\nError breakdown:")
        for error_type, count in sorted(errors.items(), key=lambda x: -x[1]):
            print(f"  - {error_type}: {count}")
    
    # Latency stats
    latencies = [r["elapsed"] for r in results if r["success"]]
    if latencies:
        print(f"\nLatency (successful queries):")
        print(f"  Average: {sum(latencies)/len(latencies):.2f}s")
        print(f"  Min: {min(latencies):.2f}s")
        print(f"  Max: {max(latencies):.2f}s")
    
    # Cleanup
    client.close()
    
    return {
        "total": len(results),
        "success": success_count,
        "amap_usage": amap_count,
        "success_rate": success_count/len(results)*100,
        "amap_rate": amap_count/len(results)*100,
    }


if __name__ == "__main__":
    result = run_stability_test()
    
    print("\n=== Summary ===")
    print(f"Success rate: {result['success_rate']:.1f}%")
    print(f"Amap MCP usage: {result['amap_rate']:.1f}%")
    
    if result['amap_rate'] < 90:
        print("\n⚠️  WARNING: Amap MCP usage below 90% target")
        print("Possible causes:")
        print("  1. MCP server returning empty responses")
        print("  2. JSON parsing errors")
        print("  3. Network timeouts")
        print("  4. API quota limits")
