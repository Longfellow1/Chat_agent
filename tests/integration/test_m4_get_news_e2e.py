"""M4 P0: get_news End-to-End Test with Fallback Validation

Tests the complete get_news integration through mcp_gateway:
1. End-to-end test through real gateway
2. Fallback mechanism validation (Mock Baidu failure)
3. Timeout handling validation

Critical for M4 completion - validates real integration, not just unit tests.
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
agent_service_path = project_root / "agent_service"
sys.path.insert(0, str(agent_service_path))

# Load environment variables
from dotenv import load_dotenv
env_file = project_root / ".env.agent"
if env_file.exists():
    load_dotenv(env_file)

from infra.tool_clients.mcp_gateway import MCPToolGateway
from infra.tool_clients.provider_base import ProviderResult
from domain.tools.types import ToolResult


def test_e2e_get_news():
    """Test 1: End-to-end get_news through mcp_gateway."""
    print("\n" + "=" * 80)
    print("Test 1: End-to-End get_news Integration")
    print("=" * 80)
    
    gateway = MCPToolGateway()
    
    # Check if provider chain is initialized
    if not hasattr(gateway, 'use_get_news_chain') or not gateway.use_get_news_chain:
        print("❌ CRITICAL: get_news provider chain not initialized!")
        print("   This means _news method is not using provider chain")
        return False
    
    print("✅ Provider chain initialized")
    
    # Test queries
    test_queries = [
        "今日股市",
        "比亚迪最新消息",
        "特斯拉降价",
    ]
    
    success_count = 0
    baidu_count = 0
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        
        start = time.time()
        result = gateway.invoke("get_news", {"topic": query})
        latency = (time.time() - start) * 1000
        
        if result.ok:
            success_count += 1
            provider = result.raw.get("provider", "unknown") if result.raw else "unknown"
            print(f"  ✅ SUCCESS | Provider: {provider} | Latency: {latency:.0f}ms")
            
            if provider == "baidu_news":
                baidu_count += 1
            
            # Check fallback chain
            if result.raw and "fallback_chain" in result.raw:
                print(f"  Fallback chain: {result.raw['fallback_chain']}")
        else:
            print(f"  ❌ FAILED | Error: {result.error}")
        
        time.sleep(1.0)  # Rate limiting
    
    print(f"\nResults: {success_count}/{len(test_queries)} successful")
    print(f"Baidu usage: {baidu_count}/{success_count}")
    
    # Validation
    if success_count < len(test_queries):
        print("❌ FAIL: Not all queries succeeded")
        return False
    
    if baidu_count == 0:
        print("❌ FAIL: Baidu provider never used (still using Tavily?)")
        return False
    
    print("✅ PASS: End-to-end integration working")
    return True


def test_fallback_mechanism():
    """Test 2: Fallback mechanism validation (Mock Baidu failure)."""
    print("\n" + "=" * 80)
    print("Test 2: Fallback Mechanism Validation")
    print("=" * 80)
    
    gateway = MCPToolGateway()
    
    if not hasattr(gateway, 'use_get_news_chain') or not gateway.use_get_news_chain:
        print("❌ SKIP: Provider chain not initialized")
        return False
    
    # Mock Baidu provider to always fail
    from infra.tool_clients.providers.baidu_news_provider import BaiduNewsProvider
    
    original_execute = BaiduNewsProvider.execute
    
    def mock_baidu_failure(self, **kwargs):
        """Mock Baidu failure to trigger fallback."""
        return ProviderResult(
            ok=False,
            data=None,
            provider_name="baidu_news",
            error="rate_limit:mocked_failure",
        )
    
    try:
        # Patch Baidu provider
        with patch.object(BaiduNewsProvider, 'execute', mock_baidu_failure):
            print("Mocked Baidu to fail, testing fallback...")
            
            result = gateway.invoke("get_news", {"topic": "今日股市"})
            
            if not result.ok:
                print(f"❌ FAIL: All providers failed")
                print(f"   Error: {result.error}")
                if result.raw and "fallback_chain" in result.raw:
                    print(f"   Fallback chain: {result.raw['fallback_chain']}")
                return False
            
            provider = result.raw.get("provider", "unknown") if result.raw else "unknown"
            print(f"✅ SUCCESS: Fallback worked, used provider: {provider}")
            
            if result.raw and "fallback_chain" in result.raw:
                fallback_chain = result.raw["fallback_chain"]
                print(f"   Fallback chain: {fallback_chain}")
                
                # Validate fallback chain
                if "baidu_news" not in str(fallback_chain):
                    print("❌ FAIL: Baidu not in fallback chain")
                    return False
                
                if provider == "baidu_news":
                    print("❌ FAIL: Still using Baidu (mock didn't work)")
                    return False
            
            print("✅ PASS: Fallback mechanism working")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timeout_handling():
    """Test 3: Timeout handling validation."""
    print("\n" + "=" * 80)
    print("Test 3: Timeout Handling Validation")
    print("=" * 80)
    
    gateway = MCPToolGateway()
    
    if not hasattr(gateway, 'use_get_news_chain') or not gateway.use_get_news_chain:
        print("❌ SKIP: Provider chain not initialized")
        return False
    
    # Check timeout configuration
    from infra.tool_clients.provider_config import load_provider_configs
    configs = load_provider_configs()
    
    if "get_news" not in configs:
        print("❌ FAIL: get_news config not found")
        return False
    
    print("Timeout configuration:")
    total_timeout = 0
    for config in configs["get_news"]:
        print(f"  {config.name}: {config.timeout}s")
        total_timeout += config.timeout
    
    print(f"Total worst-case timeout: {total_timeout}s")
    
    # Validation
    if total_timeout > 10:
        print(f"❌ FAIL: Total timeout {total_timeout}s > 10s (too slow for voice)")
        return False
    
    # Check individual timeouts
    for config in configs["get_news"]:
        if config.timeout > 3.5:
            print(f"❌ FAIL: {config.name} timeout {config.timeout}s > 3.5s")
            return False
    
    print("✅ PASS: Timeout configuration acceptable")
    return True


def main():
    """Run all P0 validation tests."""
    print("=" * 80)
    print("M4 P0: get_news End-to-End Validation")
    print("=" * 80)
    print("Critical tests for M4 completion:")
    print("1. End-to-end integration through mcp_gateway")
    print("2. Fallback mechanism (Mock Baidu failure)")
    print("3. Timeout configuration")
    print()
    
    results = []
    
    # Test 1: E2E
    results.append(("E2E Integration", test_e2e_get_news()))
    
    # Test 2: Fallback
    results.append(("Fallback Mechanism", test_fallback_mechanism()))
    
    # Test 3: Timeout
    results.append(("Timeout Configuration", test_timeout_handling()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ ALL P0 TESTS PASSED - M4 get_news integration complete")
        return 0
    else:
        print("\n❌ SOME P0 TESTS FAILED - M4 get_news NOT ready for production")
        return 1


if __name__ == "__main__":
    sys.exit(main())
