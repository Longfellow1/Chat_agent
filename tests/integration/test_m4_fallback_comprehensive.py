"""M4 Comprehensive Fallback Tests

Tests missing from P0:
1. Three-hop fallback: Baidu + Sina both fail → Tavily
2. Timeout-triggered fallback: Baidu timeout → Sina
3. Sina news quality evaluation for generic queries
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


def test_three_hop_fallback():
    """Test 1: Baidu + Sina both fail → Tavily fallback."""
    print("\n" + "=" * 80)
    print("Test 1: Three-Hop Fallback (Baidu + Sina fail → Tavily)")
    print("=" * 80)
    
    gateway = MCPToolGateway()
    
    if not hasattr(gateway, 'use_get_news_chain') or not gateway.use_get_news_chain:
        print("❌ SKIP: Provider chain not initialized")
        return False
    
    from infra.tool_clients.providers.baidu_news_provider import BaiduNewsProvider
    from infra.tool_clients.providers.sina_news_provider import SinaNewsProvider
    
    def mock_baidu_failure(self, **kwargs):
        return ProviderResult(
            ok=False,
            data=None,
            provider_name="baidu_news",
            error="rate_limit:mocked_failure",
        )
    
    def mock_sina_failure(self, **kwargs):
        return ProviderResult(
            ok=False,
            data=None,
            provider_name="sina_news",
            error="no_results:mocked_failure",
        )
    
    try:
        with patch.object(BaiduNewsProvider, 'execute', mock_baidu_failure):
            with patch.object(SinaNewsProvider, 'execute', mock_sina_failure):
                print("Mocked Baidu + Sina to fail, testing Tavily fallback...")
                
                result = gateway.invoke("get_news", {"topic": "今日股市"})
                
                if not result.ok:
                    print(f"❌ FAIL: All providers failed including Tavily")
                    print(f"   Error: {result.error}")
                    if result.raw and "fallback_chain" in result.raw:
                        print(f"   Fallback chain: {result.raw['fallback_chain']}")
                    return False
                
                provider = result.raw.get("provider", "unknown") if result.raw else "unknown"
                print(f"✅ SUCCESS: Three-hop fallback worked, used provider: {provider}")
                
                if result.raw and "fallback_chain" in result.raw:
                    fallback_chain = result.raw["fallback_chain"]
                    print(f"   Fallback chain: {fallback_chain}")
                    
                    # Validate fallback chain
                    chain_str = str(fallback_chain)
                    if "baidu_news" not in chain_str:
                        print("❌ FAIL: Baidu not in fallback chain")
                        return False
                    if "sina_news" not in chain_str:
                        print("❌ FAIL: Sina not in fallback chain")
                        return False
                    
                    if provider in ["baidu_news", "sina_news"]:
                        print(f"❌ FAIL: Still using {provider} (mock didn't work)")
                        return False
                
                print("✅ PASS: Three-hop fallback mechanism working")
                return True
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timeout_triggered_fallback():
    """Test 2: Baidu timeout → Sina fallback."""
    print("\n" + "=" * 80)
    print("Test 2: Timeout-Triggered Fallback (Baidu timeout → Sina)")
    print("=" * 80)
    
    gateway = MCPToolGateway()
    
    if not hasattr(gateway, 'use_get_news_chain') or not gateway.use_get_news_chain:
        print("❌ SKIP: Provider chain not initialized")
        return False
    
    from infra.tool_clients.providers.baidu_news_provider import BaiduNewsProvider
    
    def mock_baidu_timeout(self, **kwargs):
        """Mock Baidu timeout (not error, but timeout)."""
        time.sleep(0.1)  # Simulate some delay
        raise TimeoutError("Mocked timeout after 3s")
    
    try:
        with patch.object(BaiduNewsProvider, 'execute', mock_baidu_timeout):
            print("Mocked Baidu to timeout, testing Sina fallback...")
            
            result = gateway.invoke("get_news", {"topic": "今日股市"})
            
            if not result.ok:
                print(f"❌ FAIL: Fallback failed after timeout")
                print(f"   Error: {result.error}")
                if result.raw and "fallback_chain" in result.raw:
                    print(f"   Fallback chain: {result.raw['fallback_chain']}")
                return False
            
            provider = result.raw.get("provider", "unknown") if result.raw else "unknown"
            print(f"✅ SUCCESS: Timeout fallback worked, used provider: {provider}")
            
            if result.raw and "fallback_chain" in result.raw:
                fallback_chain = result.raw["fallback_chain"]
                print(f"   Fallback chain: {fallback_chain}")
                
                # Validate timeout was detected
                chain_str = str(fallback_chain)
                if "timeout" not in chain_str.lower() and "baidu" not in chain_str:
                    print("⚠️  WARNING: Timeout not explicitly tracked in fallback chain")
                
                if provider == "baidu_news":
                    print("❌ FAIL: Still using Baidu (timeout didn't trigger fallback)")
                    return False
            
            print("✅ PASS: Timeout-triggered fallback working")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sina_news_quality():
    """Test 3: Sina news quality for generic queries."""
    print("\n" + "=" * 80)
    print("Test 3: Sina News Quality Evaluation")
    print("=" * 80)
    
    from infra.tool_clients.providers.sina_news_provider import SinaNewsProvider
    from infra.tool_clients.provider_base import ProviderConfig
    
    config = ProviderConfig(
        name="sina_news",
        priority=2,
        timeout=3.0,
        max_retries=1,
    )
    
    provider = SinaNewsProvider(config)
    
    # Test queries: financial (good) vs generic (potentially bad)
    test_cases = [
        ("今日股市", "financial", True),  # Should work well
        ("美联储加息", "financial", True),  # Should work well
        ("iPhone新品", "tech", False),  # May not work well
        ("特斯拉动态", "auto", False),  # May not work well
        ("汽车芯片", "auto", False),  # May not work well
    ]
    
    results = []
    
    for query, category, expected_good in test_cases:
        print(f"\nTesting: {query} ({category})")
        
        result = provider.execute(query=query)
        
        if result.ok and result.data:
            news_count = len(result.data.raw.get("results", [])) if result.data.raw else 0
            print(f"  ✅ SUCCESS: {news_count} results")
            
            # Check if results are relevant
            if result.data.text:
                text_lower = result.data.text.lower()
                query_lower = query.lower()
                
                # Simple relevance check
                relevant = any(word in text_lower for word in query_lower.split())
                print(f"  Relevance: {'✅ Good' if relevant else '❌ Poor'}")
                
                results.append({
                    "query": query,
                    "category": category,
                    "expected_good": expected_good,
                    "success": True,
                    "relevant": relevant,
                })
        else:
            print(f"  ❌ FAILED: {result.error}")
            results.append({
                "query": query,
                "category": category,
                "expected_good": expected_good,
                "success": False,
                "relevant": False,
            })
        
        time.sleep(1.0)  # Rate limiting
    
    # Analysis
    print("\n" + "-" * 80)
    print("ANALYSIS:")
    
    financial_success = sum(1 for r in results if r["category"] == "financial" and r["success"])
    non_financial_success = sum(1 for r in results if r["category"] != "financial" and r["success"])
    
    print(f"Financial queries: {financial_success}/2 successful")
    print(f"Non-financial queries: {non_financial_success}/3 successful")
    
    # Conclusion
    if financial_success == 2 and non_financial_success < 2:
        print("\n⚠️  WARNING: Sina news works well for financial queries but poor for generic queries")
        print("   Recommendation: Consider replacing Sina with 博查 or mcp-hotnews-server for get_news")
        print("   Keep Sina for get_stock chain instead")
        return "warning"
    elif financial_success == 2 and non_financial_success >= 2:
        print("\n✅ PASS: Sina news works well for both financial and generic queries")
        return True
    else:
        print("\n❌ FAIL: Sina news quality is poor even for financial queries")
        return False


def main():
    """Run comprehensive fallback tests."""
    print("=" * 80)
    print("M4 Comprehensive Fallback Tests")
    print("=" * 80)
    print("Missing tests from P0:")
    print("1. Three-hop fallback (Baidu + Sina fail → Tavily)")
    print("2. Timeout-triggered fallback (Baidu timeout → Sina)")
    print("3. Sina news quality evaluation")
    print()
    
    results = []
    
    # Test 1: Three-hop fallback
    results.append(("Three-Hop Fallback", test_three_hop_fallback()))
    
    # Test 2: Timeout fallback
    results.append(("Timeout Fallback", test_timeout_triggered_fallback()))
    
    # Test 3: Sina quality
    sina_result = test_sina_news_quality()
    results.append(("Sina News Quality", sina_result))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for name, result in results:
        if result == "warning":
            status = "⚠️  WARNING"
        elif result:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    
    # Overall assessment
    passed = sum(1 for _, r in results if r is True)
    warnings = sum(1 for _, r in results if r == "warning")
    failed = sum(1 for _, r in results if r is False)
    
    print(f"Passed: {passed}/{len(results)}")
    print(f"Warnings: {warnings}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    
    if failed == 0 and warnings == 0:
        print("\n✅ ALL COMPREHENSIVE TESTS PASSED")
        return 0
    elif failed == 0:
        print("\n⚠️  TESTS PASSED WITH WARNINGS - Review recommendations")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
