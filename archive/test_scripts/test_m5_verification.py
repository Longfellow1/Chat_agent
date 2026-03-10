"""M5 Verification - 验证三个关键问题"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_1_get_news_new_chain():
    """验证1: get_news 新链路测试 (Sina → Tavily)"""
    print("\n" + "=" * 60)
    print("验证1: get_news 新链路测试 (Sina → Tavily)")
    print("=" * 60)
    
    from agent_service.infra.tool_clients.mcp_gateway import MCPToolGateway
    
    gateway = MCPToolGateway()
    
    test_queries = [
        # 科技新闻 (7条)
        "今天科技新闻",
        "人工智能最新进展",
        "苹果新品发布",
        "华为芯片突破",
        "5G技术应用",
        "量子计算机研究",
        "SpaceX火箭发射",
        
        # 汽车新闻 (7条)
        "今天汽车新闻",
        "比亚迪最新消息",
        "特斯拉股价",
        "新能源汽车政策",
        "自动驾驶技术",
        "电动汽车补贴",
        "车展最新动态",
        
        # 财经新闻 (6条)
        "今日财经新闻",
        "股市行情",
        "美联储加息",
        "人民币汇率",
        "房地产市场",
        "黄金价格走势",
    ]
    
    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/20] 查询: {query}")
        try:
            start = time.time()
            result = gateway.get_news(query=query)
            latency = (time.time() - start) * 1000
            
            if result.ok:
                provider = result.raw.get('provider', 'unknown')
                text_preview = result.text[:100] if result.text else ""
                print(f"✅ 成功 | Provider: {provider} | 延迟: {latency:.0f}ms")
                print(f"   内容预览: {text_preview}...")
                results.append({
                    'query': query,
                    'success': True,
                    'provider': provider,
                    'latency_ms': latency,
                    'text': result.text,
                })
            else:
                print(f"❌ 失败: {result.text}")
                results.append({
                    'query': query,
                    'success': False,
                    'error': result.text,
                })
        except Exception as e:
            print(f"❌ 异常: {e}")
            results.append({
                'query': query,
                'success': False,
                'error': str(e),
            })
    
    # 统计
    success_count = sum(1 for r in results if r.get('success'))
    sina_count = sum(1 for r in results if r.get('provider') == 'sina_news')
    tavily_count = sum(1 for r in results if r.get('provider') == 'tavily')
    
    print(f"\n" + "=" * 60)
    print(f"成功率: {success_count}/20 ({success_count/20*100:.1f}%)")
    print(f"Sina使用率: {sina_count}/20 ({sina_count/20*100:.1f}%)")
    print(f"Tavily使用率: {tavily_count}/20 ({tavily_count/20*100:.1f}%)")
    
    if success_count > 0:
        latencies = [r['latency_ms'] for r in results if r.get('success')]
        print(f"平均延迟: {sum(latencies)/len(latencies):.0f}ms")
    
    return results


def test_2_ttft_benchmark():
    """验证2: TTFT基准测试 (5条完整查询)"""
    print("\n" + "=" * 60)
    print("验证2: TTFT基准测试 (端到端延迟)")
    print("=" * 60)
    
    from agent_service.app.orchestrator.chat_flow import ChatFlow
    from agent_service.domain.tools.types import ChatRequest
    
    chat_flow = ChatFlow()
    
    test_queries = [
        "北京今天天气怎么样",
        "今天汽车新闻",
        "比亚迪股价",
        "附近停车场",
        "特斯拉最新消息",
    ]
    
    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/5] 查询: {query}")
        try:
            request = ChatRequest(
                query=query,
                session_id=f"ttft_test_{i}",
            )
            
            start = time.time()
            response = chat_flow.run(request)
            total_latency = (time.time() - start) * 1000
            
            print(f"✅ 完成")
            print(f"   决策模式: {response.decision_mode}")
            print(f"   工具: {response.tool_name if response.tool_name else 'N/A'}")
            print(f"   总延迟: {total_latency:.0f}ms")
            
            if hasattr(response, 'latency_ms'):
                print(f"   工具延迟: {response.latency_ms.tool_call if hasattr(response.latency_ms, 'tool_call') else 'N/A'}ms")
            
            results.append({
                'query': query,
                'success': True,
                'total_latency_ms': total_latency,
                'decision_mode': response.decision_mode,
                'tool_name': response.tool_name,
            })
        except Exception as e:
            print(f"❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'query': query,
                'success': False,
                'error': str(e),
            })
    
    # 统计
    success_count = sum(1 for r in results if r.get('success'))
    if success_count > 0:
        latencies = [r['total_latency_ms'] for r in results if r.get('success')]
        avg_latency = sum(latencies) / len(latencies)
        p50_latency = sorted(latencies)[len(latencies)//2]
        
        print(f"\n" + "=" * 60)
        print(f"成功率: {success_count}/5 ({success_count/5*100:.1f}%)")
        print(f"平均延迟: {avg_latency:.0f}ms")
        print(f"P50延迟: {p50_latency:.0f}ms")
        print(f"最大延迟: {max(latencies):.0f}ms")
        print(f"最小延迟: {min(latencies):.0f}ms")
        
        if p50_latency <= 2000:
            print(f"✅ P50延迟 {p50_latency:.0f}ms <= 2000ms (达标)")
        else:
            print(f"❌ P50延迟 {p50_latency:.0f}ms > 2000ms (不达标)")
    
    return results


def test_3_content_rewriter_real_data():
    """验证3: Content Rewriter 真实数据测试"""
    print("\n" + "=" * 60)
    print("验证3: Content Rewriter 真实数据测试")
    print("=" * 60)
    
    from agent_service.infra.tool_clients.content_rewriter import ContentRewriter, RewriteConfig
    
    rewriter = ContentRewriter(
        llm_client=None,
        config=RewriteConfig(enable_llm=False)
    )
    
    # 真实新闻内容（模拟Sina返回）
    real_news_content = """已搜索新闻：比亚迪最新消息

1. 比亚迪发布新能源汽车新车型 (2026-03-07) [新浪财经]
   https://finance.sina.com.cn/stock/relnews/cn/2026-03-07/doc-abc123.shtml
   比亚迪今日发布新能源汽车新车型，预计售价20万元起。[查看原文](https://finance.sina.com.cn/stock/relnews/cn/2026-03-07/doc-abc123.shtml) \\n\\n 更多详情请访问官网。

2. 比亚迪股价上涨5% (2026-03-06) [新浪财经]
   https://finance.sina.com.cn/stock/relnews/cn/2026-03-06/doc-def456.shtml
   受新车型发布消息影响，比亚迪股价今日上涨5%。\\t 阅读全文 https://finance.sina.com.cn/stock/relnews/cn/2026-03-06/doc-def456.shtml

3. 比亚迪海外市场扩张 (2026-03-05) [新浪财经]
   https://finance.sina.com.cn/stock/relnews/cn/2026-03-05/doc-ghi789.shtml
   比亚迪宣布进军欧洲市场，计划在德国建厂。[更多详情](https://finance.sina.com.cn/stock/relnews/cn/2026-03-05/doc-ghi789.shtml) \\n\\n 查看原文了解更多。"""
    
    print("\n原始内容:")
    print("-" * 60)
    print(real_news_content)
    print("-" * 60)
    
    # 测试清理
    print("\n开始清理...")
    latencies = []
    for i in range(100):
        start = time.time()
        cleaned = rewriter.rewrite_news(real_news_content)
        latency = (time.time() - start) * 1000
        latencies.append(latency)
    
    print(f"\n清理后内容:")
    print("-" * 60)
    print(cleaned)
    print("-" * 60)
    
    # 验证清理效果
    print("\n清理效果验证:")
    checks = {
        "URL清理": "http" not in cleaned and "https" not in cleaned,
        "转义字符清理": "\\n" not in cleaned and "\\t" not in cleaned,
        "噪声词清理": "查看原文" not in cleaned and "更多详情" not in cleaned and "阅读全文" not in cleaned,
        "Markdown链接清理": "[" not in cleaned or "](" not in cleaned,
    }
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}: {'通过' if passed else '失败'}")
    
    # 延迟统计
    avg_latency = sum(latencies) / len(latencies)
    p50_latency = sorted(latencies)[len(latencies)//2]
    p95_latency = sorted(latencies)[int(len(latencies)*0.95)]
    p99_latency = sorted(latencies)[int(len(latencies)*0.99)]
    
    print(f"\n延迟统计 (100次测试):")
    print(f"平均延迟: {avg_latency:.3f}ms")
    print(f"P50延迟: {p50_latency:.3f}ms")
    print(f"P95延迟: {p95_latency:.3f}ms")
    print(f"P99延迟: {p99_latency:.3f}ms")
    print(f"最大延迟: {max(latencies):.3f}ms")
    print(f"最小延迟: {min(latencies):.3f}ms")
    
    return {
        'original': real_news_content,
        'cleaned': cleaned,
        'checks': checks,
        'latencies': {
            'avg': avg_latency,
            'p50': p50_latency,
            'p95': p95_latency,
            'p99': p99_latency,
            'max': max(latencies),
            'min': min(latencies),
        }
    }


def main():
    """运行所有验证"""
    print("\n" + "=" * 60)
    print("M5 关键问题验证")
    print("=" * 60)
    
    # 验证1: get_news 新链路
    print("\n\n")
    news_results = test_1_get_news_new_chain()
    
    # 验证2: TTFT基准
    print("\n\n")
    ttft_results = test_2_ttft_benchmark()
    
    # 验证3: Content Rewriter 真实数据
    print("\n\n")
    rewriter_results = test_3_content_rewriter_real_data()
    
    # 总结
    print("\n\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    news_success = sum(1 for r in news_results if r.get('success'))
    ttft_success = sum(1 for r in ttft_results if r.get('success'))
    rewriter_all_passed = all(rewriter_results['checks'].values())
    
    print(f"\n1. get_news 新链路: {news_success}/20 成功 ({news_success/20*100:.1f}%)")
    print(f"2. TTFT基准: {ttft_success}/5 成功 ({ttft_success/5*100:.1f}%)")
    print(f"3. Content Rewriter: {'✅ 全部通过' if rewriter_all_passed else '❌ 部分失败'}")
    
    if news_success >= 18 and ttft_success >= 4 and rewriter_all_passed:
        print("\n🎉 所有验证通过！")
        return 0
    else:
        print("\n⚠️ 部分验证未通过，需要修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
