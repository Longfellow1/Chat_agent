"""M5 Final Validation Test - 验证所有M5功能"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_m5_1_find_nearby():
    """Test M5.1: find_nearby Provider Chain"""
    print("\n" + "=" * 60)
    print("M5.1: Testing find_nearby Provider Chain")
    print("=" * 60)
    
    from agent_service.infra.tool_clients.mcp_gateway import MCPToolGateway
    
    gateway = MCPToolGateway()
    
    test_queries = [
        "附近停车场",
        "上海附近餐厅",
        "国家会展中心附近充电桩",
    ]
    
    success_count = 0
    for query in test_queries:
        print(f"\n查询: {query}")
        try:
            result = gateway.find_nearby(query=query, city="上海")
            if result.ok:
                print(f"✅ 成功")
                print(f"Provider: {result.raw.get('provider', 'unknown')}")
                success_count += 1
            else:
                print(f"❌ 失败: {result.text}")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print(f"\n成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    return success_count == len(test_queries)


def test_m5_2_get_weather():
    """Test M5.2: get_weather Provider Chain"""
    print("\n" + "=" * 60)
    print("M5.2: Testing get_weather Provider Chain")
    print("=" * 60)
    
    from agent_service.infra.tool_clients.mcp_gateway import MCPToolGateway
    
    gateway = MCPToolGateway()
    
    test_queries = [
        "北京今天天气",
        "上海明天会下雨吗",
        "深圳这周天气",
    ]
    
    success_count = 0
    for query in test_queries:
        print(f"\n查询: {query}")
        try:
            result = gateway.get_weather(query=query)
            if result.ok:
                print(f"✅ 成功")
                print(f"Provider: {result.raw.get('provider', 'unknown')}")
                success_count += 1
            else:
                print(f"❌ 失败: {result.text}")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print(f"\n成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    return success_count == len(test_queries)


def test_m5_3_content_rewriter():
    """Test M5.3: Content Rewriter Integration"""
    print("\n" + "=" * 60)
    print("M5.3: Testing Content Rewriter Integration")
    print("=" * 60)
    
    from agent_service.infra.tool_clients.content_rewriter import ContentRewriter, RewriteConfig
    
    rewriter = ContentRewriter(
        llm_client=None,
        config=RewriteConfig(enable_llm=False)
    )
    
    test_cases = [
        {
            "input": "【财经新闻】比亚迪发布新车型 [查看原文](https://example.com) \\n\\n 更多详情...",
            "should_not_contain": ["http", "\\n", "查看原文"],
        },
        {
            "input": "特斯拉股价上涨 https://example.com \\t 阅读全文",
            "should_not_contain": ["http", "\\t", "阅读全文"],
        },
        {
            "input": "新能源汽车政策发布 [更多详情](https://...) \\n\\n",
            "should_not_contain": ["http", "\\n", "更多详情"],
        },
    ]
    
    success_count = 0
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}:")
        print(f"输入: {case['input'][:50]}...")
        
        try:
            cleaned = rewriter.rewrite_news(case['input'])
            print(f"输出: {cleaned[:50]}...")
            
            # Check if unwanted content is removed
            all_removed = all(
                unwanted not in cleaned
                for unwanted in case['should_not_contain']
            )
            
            if all_removed:
                print(f"✅ 清理成功")
                success_count += 1
            else:
                print(f"❌ 清理失败: 仍包含噪声内容")
                for unwanted in case['should_not_contain']:
                    if unwanted in cleaned:
                        print(f"  - 残留: {unwanted}")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print(f"\n成功率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)


def test_provider_chain_config():
    """Test Provider Chain Configuration"""
    print("\n" + "=" * 60)
    print("Testing Provider Chain Configuration")
    print("=" * 60)
    
    from agent_service.infra.tool_clients.provider_config import PROVIDER_CONFIGS
    
    # Check get_news config (should not have baidu_news)
    get_news_providers = [p.name for p in PROVIDER_CONFIGS.get("get_news", [])]
    print(f"\nget_news providers: {get_news_providers}")
    
    if "baidu_news" in get_news_providers:
        print("❌ 错误: baidu_news 仍在配置中（应该已废弃）")
        return False
    
    if "sina_news" not in get_news_providers:
        print("❌ 错误: sina_news 不在配置中")
        return False
    
    print("✅ get_news 配置正确")
    
    # Check find_nearby config
    find_nearby_providers = [p.name for p in PROVIDER_CONFIGS.get("find_nearby", [])]
    print(f"\nfind_nearby providers: {find_nearby_providers}")
    
    if "amap_mcp" not in find_nearby_providers:
        print("❌ 错误: amap_mcp 不在配置中")
        return False
    
    print("✅ find_nearby 配置正确")
    
    # Check get_weather config
    get_weather_providers = [p.name for p in PROVIDER_CONFIGS.get("get_weather", [])]
    print(f"\nget_weather providers: {get_weather_providers}")
    
    if "amap_mcp" not in get_weather_providers:
        print("❌ 错误: amap_mcp 不在配置中")
        return False
    
    print("✅ get_weather 配置正确")
    
    return True


def main():
    """Run all M5 validation tests"""
    print("\n" + "=" * 60)
    print("M5 FINAL VALIDATION TEST")
    print("=" * 60)
    
    results = {
        "M5.1 find_nearby": test_m5_1_find_nearby(),
        "M5.2 get_weather": test_m5_2_get_weather(),
        "M5.3 Content Rewriter": test_m5_3_content_rewriter(),
        "Provider Chain Config": test_provider_chain_config(),
    }
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 M5 全部验证通过！车展准备就绪！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，需要修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
