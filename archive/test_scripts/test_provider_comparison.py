"""
搜索 Provider 对比测试

对比 Tavily、Bing MCP、阿里云 IQS 三个 Provider 的：
1. 响应速度
2. 结果质量（字段完整性、内容质量）
3. 成本效益
"""
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.providers.tavily_provider import TavilyProvider
from infra.tool_clients.providers.bing_mcp_provider import BingMCPProvider
from infra.tool_clients.providers.aliyun_iqs_provider import AliyunIQSProvider
from infra.tool_clients.provider_base import ProviderConfig


# 测试查询集
TEST_QUERIES = [
    "特斯拉最新消息",
    "iPhone 15价格",
    "2026年世界杯",
    "量子计算原理",
    "杭州西湖旅游攻略",
]


def test_provider(provider, provider_name, query):
    """测试单个 Provider"""
    print(f"\n{'='*60}")
    print(f"Provider: {provider_name}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = provider.execute(query=query)
        
        elapsed = time.time() - start_time
        
        if not result.ok:
            print(f"❌ 错误: {result.error}")
            print(f"⏱️  耗时: {elapsed:.2f}s")
            return {
                "provider": provider_name,
                "query": query,
                "success": False,
                "error": result.error,
                "elapsed": elapsed,
            }
        
        # 提取结果
        raw_results = []
        if result.data and hasattr(result.data, 'raw') and 'results' in result.data.raw:
            raw_results = result.data.raw['results']
        
        print(f"✅ 成功")
        print(f"⏱️  耗时: {elapsed:.2f}s")
        print(f"📊 结果数: {len(raw_results)}")
        
        # 分析字段完整性
        if raw_results:
            print(f"\n📝 Top 3 结果:")
            for i, item in enumerate(raw_results[:3], 1):
                title = item.get('title', 'N/A')
                url = item.get('url', 'N/A')
                content = item.get('content', '')
                published_date = item.get('published_date') or item.get('publishedDate')
                
                print(f"\n{i}. {title[:60]}")
                print(f"   URL: {url[:80]}")
                print(f"   Content: {content[:100] if content else '[无内容]'}...")
                print(f"   Published: {published_date if published_date else '[无日期]'}")
        
        # 统计字段完整性
        has_url = sum(1 for r in raw_results if r.get('url'))
        has_content = sum(1 for r in raw_results if r.get('content') or r.get('summary'))
        has_date = sum(1 for r in raw_results if r.get('published_date') or r.get('publishedDate'))
        
        print(f"\n📈 字段完整性:")
        print(f"   URL: {has_url}/{len(raw_results)} ({has_url/len(raw_results)*100:.0f}%)")
        print(f"   Content: {has_content}/{len(raw_results)} ({has_content/len(raw_results)*100:.0f}%)")
        print(f"   Date: {has_date}/{len(raw_results)} ({has_date/len(raw_results)*100:.0f}%)")
        
        return {
            "provider": provider_name,
            "query": query,
            "success": True,
            "elapsed": elapsed,
            "result_count": len(raw_results),
            "field_completeness": {
                "url": has_url / len(raw_results) if raw_results else 0,
                "content": has_content / len(raw_results) if raw_results else 0,
                "date": has_date / len(raw_results) if raw_results else 0,
            },
            "top_result": raw_results[0] if raw_results else None,
        }
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 异常: {e}")
        print(f"⏱️  耗时: {elapsed:.2f}s")
        return {
            "provider": provider_name,
            "query": query,
            "success": False,
            "error": str(e),
            "elapsed": elapsed,
        }


def main():
    """主函数"""
    print("="*80)
    print("搜索 Provider 对比测试")
    print("="*80)
    
    # 初始化 Providers
    providers = []
    
    # Tavily
    if os.getenv("TAVILY_API_KEY"):
        tavily_config = ProviderConfig(
            name="tavily",
            priority=1,
            enabled=True,
            timeout=30,
        )
        providers.append(("Tavily", TavilyProvider(tavily_config)))
    else:
        print("⚠️  Tavily API Key 未设置，跳过")
    
    # Bing MCP
    if os.getenv("BING_API_KEY"):
        bing_config = ProviderConfig(
            name="bing_mcp",
            priority=2,
            enabled=True,
            timeout=30,
        )
        providers.append(("Bing MCP", BingMCPProvider(bing_config)))
    else:
        print("⚠️  Bing API Key 未设置，跳过")
    
    # 阿里云 IQS
    if os.getenv("ALIYUN_IQS_API_KEY"):
        iqs_config = ProviderConfig(
            name="aliyun_iqs",
            priority=3,
            enabled=True,
            timeout=30,
        )
        providers.append(("阿里云 IQS", AliyunIQSProvider(iqs_config)))
    else:
        print("⚠️  阿里云 IQS API Key 未设置，跳过")
    
    if not providers:
        print("❌ 没有可用的 Provider，请设置 API Key")
        return
    
    # 执行测试
    all_results = []
    
    for query in TEST_QUERIES:
        print(f"\n\n{'#'*80}")
        print(f"# 查询: {query}")
        print(f"{'#'*80}")
        
        for provider_name, provider in providers:
            result = test_provider(provider, provider_name, query)
            all_results.append(result)
            time.sleep(1)  # 避免请求过快
    
    # 生成对比报告
    generate_comparison_report(all_results)


def generate_comparison_report(results):
    """生成对比报告"""
    print(f"\n\n{'='*80}")
    print("对比报告")
    print(f"{'='*80}\n")
    
    # 按 Provider 分组
    by_provider = {}
    for r in results:
        provider = r['provider']
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(r)
    
    # 统计各 Provider 的表现
    print("## 1. 整体表现\n")
    print(f"{'Provider':<20} {'成功率':<10} {'平均耗时':<12} {'平均结果数':<12}")
    print("-" * 60)
    
    for provider, provider_results in by_provider.items():
        success_count = sum(1 for r in provider_results if r['success'])
        success_rate = success_count / len(provider_results) * 100
        
        avg_elapsed = sum(r['elapsed'] for r in provider_results) / len(provider_results)
        
        successful_results = [r for r in provider_results if r['success']]
        avg_result_count = sum(r.get('result_count', 0) for r in successful_results) / len(successful_results) if successful_results else 0
        
        print(f"{provider:<20} {success_rate:>6.1f}%    {avg_elapsed:>8.2f}s     {avg_result_count:>8.1f}")
    
    # 字段完整性对比
    print(f"\n## 2. 字段完整性\n")
    print(f"{'Provider':<20} {'URL':<10} {'Content':<10} {'Date':<10}")
    print("-" * 50)
    
    for provider, provider_results in by_provider.items():
        successful_results = [r for r in provider_results if r['success'] and 'field_completeness' in r]
        
        if successful_results:
            avg_url = sum(r['field_completeness']['url'] for r in successful_results) / len(successful_results) * 100
            avg_content = sum(r['field_completeness']['content'] for r in successful_results) / len(successful_results) * 100
            avg_date = sum(r['field_completeness']['date'] for r in successful_results) / len(successful_results) * 100
            
            print(f"{provider:<20} {avg_url:>6.1f}%    {avg_content:>6.1f}%    {avg_date:>6.1f}%")
    
    print(f"\n{'='*80}")
    print("测试完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
