"""Test Baidu API with real key."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent_service"))

# Set real key
os.environ["BAIDU_BCE_ACCESS_KEY"] = "REDACTED"

from domain.intents.encyclopedia_router import EncyclopediaRouter
from infra.tool_clients.mcp_gateway import MCPToolGateway


def test_baidu_baike():
    """Test Baidu Baike with real key."""
    print("=" * 60)
    print("测试百度百科")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    query = "什么是电动汽车"
    print(f"\n查询: {query}")
    print("-" * 60)
    
    try:
        result = gateway.invoke("encyclopedia", {"query": query})
        
        if result.ok:
            print(f"✓ 成功")
            print(f"Provider: {result.raw.get('provider_name', 'unknown')}")
            print(f"\n结果:\n{result.text}\n")
        else:
            print(f"✗ 失败: {result.error}")
            if result.raw:
                print(f"详情: {result.raw}")
    except Exception as e:
        print(f"✗ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_baidu_search_mcp():
    """Test Baidu Search MCP with real key."""
    print("=" * 60)
    print("测试百度搜索 MCP")
    print("=" * 60)
    
    gateway = MCPToolGateway()
    
    query = "特斯拉 Model 3 价格"
    print(f"\n查询: {query}")
    print("-" * 60)
    
    try:
        result = gateway.invoke("web_search", {"query": query})
        
        if result.ok:
            print(f"✓ 成功")
            print(f"Provider: {result.raw.get('provider_name', 'unknown')}")
            print(f"\n结果:\n{result.text[:500]}\n")
        else:
            print(f"✗ 失败: {result.error}")
            if result.raw:
                print(f"详情: {result.raw}")
    except Exception as e:
        print(f"✗ 异常: {e}")
        import traceback
        traceback.print_exc()


def test_router():
    """Test encyclopedia router."""
    print("=" * 60)
    print("测试查询路由器")
    print("=" * 60)
    
    router = EncyclopediaRouter()
    
    test_cases = [
        ("什么是电动汽车", "encyclopedia"),
        ("特斯拉 Model 3 价格", "web_search"),
        ("马斯克是谁", "encyclopedia"),
        ("比亚迪最新消息", "web_search"),
    ]
    
    for query, expected in test_cases:
        result = router.route(query)
        status = "✓" if result == expected else "✗"
        print(f"{status} {query:25s} → {result:15s}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("百度 API 真实测试")
    print("=" * 60 + "\n")
    
    # Test router first
    test_router()
    
    # Test Baidu Baike
    test_baidu_baike()
    
    # Test Baidu Search MCP
    test_baidu_search_mcp()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
