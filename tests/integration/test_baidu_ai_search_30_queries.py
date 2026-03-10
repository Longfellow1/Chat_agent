#!/usr/bin/env python3
"""测试百度 AI 搜索在 30 条联网搜索测试集上的召回效果"""

import csv
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.providers.baidu_providers import BaiduAISearchProvider

# 设置 API Key
os.environ["BAIDU_QIANFAN_API_KEY"] = "REDACTED"

def load_test_queries():
    """加载测试查询"""
    queries = []
    csv_path = Path(__file__).parent.parent.parent / "web_search_30_queries.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row['query'])
    
    return queries

def test_baidu_ai_search():
    """测试百度 AI 搜索"""
    
    # 创建 provider
    config = ProviderConfig(
        name="baidu_ai_search",
        priority=1,
        timeout=15.0,
        enabled=True,
    )
    
    provider = BaiduAISearchProvider(config)
    
    # 健康检查
    if not provider.health_check():
        print("❌ Provider 健康检查失败")
        return
    
    print("✅ Provider 健康检查通过")
    
    # 加载测试查询
    queries = load_test_queries()
    
    print(f"\n{'='*80}")
    print(f"百度 AI 搜索召回效果测试 - {len(queries)} 条查询")
    print(f"{'='*80}\n")
    
    results = []
    success_count = 0
    rate_limit_count = 0
    error_count = 0
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {query}")
        
        try:
            start_time = time.time()
            result = provider.execute(query=query)
            latency = (time.time() - start_time) * 1000
            
            if result.ok:
                success_count += 1
                status = "✅"
                
                # 显示响应内容（截断）
                content = result.data.text
                if len(content) > 200:
                    content = content[:200] + "..."
                
                print(f"  {status} 成功 ({latency:.0f}ms)")
                print(f"  内容: {content}")
                
                results.append({
                    "query": query,
                    "status": "success",
                    "latency_ms": latency,
                    "content": result.data.text,
                    "error": None
                })
                
            else:
                # 检查错误类型
                if "rate_limit" in result.error:
                    rate_limit_count += 1
                    status = "⏸️"
                    print(f"  {status} 速率限制: {result.error}")
                else:
                    error_count += 1
                    status = "❌"
                    print(f"  {status} 失败: {result.error}")
                
                results.append({
                    "query": query,
                    "status": "rate_limit" if "rate_limit" in result.error else "error",
                    "latency_ms": latency,
                    "content": None,
                    "error": result.error
                })
            
            # 避免触发速率限制，添加延迟
            if i < len(queries):
                time.sleep(2)
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ 异常: {str(e)}")
            results.append({
                "query": query,
                "status": "exception",
                "latency_ms": 0,
                "content": None,
                "error": str(e)
            })
        
        print()
    
    # 统计结果
    print(f"{'='*80}")
    print("测试结果统计")
    print(f"{'='*80}\n")
    
    total = len(queries)
    success_rate = (success_count / total * 100) if total > 0 else 0
    
    print(f"总查询数: {total}")
    print(f"成功: {success_count} ({success_rate:.1f}%)")
    print(f"速率限制: {rate_limit_count}")
    print(f"错误: {error_count}")
    
    # 计算平均延迟
    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        avg_latency = sum(r["latency_ms"] for r in successful_results) / len(successful_results)
        print(f"\n平均延迟: {avg_latency:.0f}ms")
    
    # 显示失败案例
    failed_results = [r for r in results if r["status"] in ["error", "exception"]]
    if failed_results:
        print(f"\n失败案例 ({len(failed_results)}条):")
        for r in failed_results:
            print(f"  - {r['query']}")
            print(f"    错误: {r['error']}")
    
    # 显示速率限制案例
    if rate_limit_count > 0:
        print(f"\n⚠️ 遇到 {rate_limit_count} 次速率限制")
        print("说明：")
        print("  - API 端点和认证都正确")
        print("  - 需要等待限流解除或提高配额")
        print("  - 建议在 Provider Chain 中配置 fallback")
    
    # 保存详细结果
    report_path = Path(__file__).parent / "baidu_ai_search_30_queries_report.md"
    save_report(results, report_path)
    print(f"\n详细报告已保存到: {report_path}")
    
    return results

def save_report(results, report_path):
    """保存测试报告"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 百度 AI 搜索召回效果测试报告\n\n")
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 统计
        total = len(results)
        success = sum(1 for r in results if r["status"] == "success")
        rate_limit = sum(1 for r in results if r["status"] == "rate_limit")
        error = sum(1 for r in results if r["status"] in ["error", "exception"])
        
        f.write("## 测试统计\n\n")
        f.write(f"- 总查询数: {total}\n")
        f.write(f"- 成功: {success} ({success/total*100:.1f}%)\n")
        f.write(f"- 速率限制: {rate_limit}\n")
        f.write(f"- 错误: {error}\n\n")
        
        # 平均延迟
        successful_results = [r for r in results if r["status"] == "success"]
        if successful_results:
            avg_latency = sum(r["latency_ms"] for r in successful_results) / len(successful_results)
            f.write(f"- 平均延迟: {avg_latency:.0f}ms\n\n")
        
        # 详细结果
        f.write("## 详细结果\n\n")
        
        for i, r in enumerate(results, 1):
            status_icon = {
                "success": "✅",
                "rate_limit": "⏸️",
                "error": "❌",
                "exception": "❌"
            }.get(r["status"], "❓")
            
            f.write(f"### {i}. {r['query']}\n\n")
            f.write(f"- 状态: {status_icon} {r['status']}\n")
            
            if r["status"] == "success":
                f.write(f"- 延迟: {r['latency_ms']:.0f}ms\n")
                f.write(f"- 内容:\n\n```\n{r['content']}\n```\n\n")
            else:
                f.write(f"- 错误: {r['error']}\n\n")
        
        # 结论
        f.write("## 结论\n\n")
        
        if success > 0:
            f.write(f"百度 AI 搜索成功处理了 {success}/{total} 条查询，召回率为 {success/total*100:.1f}%。\n\n")
        
        if rate_limit > 0:
            f.write(f"⚠️ 遇到 {rate_limit} 次速率限制，说明 API 端点和认证都正确，只是触发了配额限制。\n\n")
        
        if error > 0:
            f.write(f"❌ 有 {error} 条查询失败，需要进一步分析错误原因。\n\n")
        
        f.write("### 建议\n\n")
        f.write("1. 在 Provider Chain 中配置 fallback 机制\n")
        f.write("2. 调整请求频率以避免速率限制\n")
        f.write("3. 考虑提高 API 配额\n")
        f.write("4. 监控错误类型并优化错误处理\n")

if __name__ == "__main__":
    test_baidu_ai_search()
