"""M5.3 Content Rewriter 集成测试"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from agent_service.infra.tool_clients.mcp_gateway import MCPToolGateway
from agent_service.infra.tool_clients.content_rewriter import ContentRewriter, RewriteConfig

def test_content_rewriter_integration():
    """测试Content Rewriter集成到get_news工具"""
    gateway = MCPToolGateway()
    
    print("=" * 80)
    print("M5.3 Content Rewriter 集成测试")
    print("=" * 80)
    
    test_queries = [
        "今天汽车新闻",
        "比亚迪最新消息",
        "新能源汽车政策",
        "特斯拉股价",
        "车展最新动态",
    ]
    
    success_count = 0
    cleaned_count = 0
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        print("-" * 60)
        
        result = gateway.invoke("get_news", {"topic": query})
        
        if result.ok:
            success_count += 1
            
            # 检查清理效果
            has_url = "http" in result.text or "https" in result.text
            has_escape = "\\n" in result.text or "\\t" in result.text
            has_noise = "查看原文" in result.text or "更多详情" in result.text
            
            if not has_url and not has_escape and not has_noise:
                cleaned_count += 1
                print(f"✅ 清理成功")
            else:
                print(f"⚠️  清理不完整:")
                if has_url:
                    print(f"   - 仍有URL")
                if has_escape:
                    print(f"   - 仍有转义字符")
                if has_noise:
                    print(f"   - 仍有噪声词")
            
            print(f"Text: {result.text[:200]}...")
        else:
            print(f"❌ 失败: {result.error}")
    
    print("\n" + "=" * 80)
    print(f"测试结果:")
    print(f"  成功率: {success_count}/{len(test_queries)} ({success_count*100//len(test_queries)}%)")
    print(f"  清理率: {cleaned_count}/{success_count} ({cleaned_count*100//success_count if success_count > 0 else 0}%)")
    print("=" * 80)

if __name__ == "__main__":
    test_content_rewriter_integration()
