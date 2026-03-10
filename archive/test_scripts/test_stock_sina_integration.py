"""测试新浪财经集成到mcp_gateway"""
import sys
sys.path.insert(0, 'agent_service')

from infra.tool_clients.mcp_gateway import MCPToolGateway

gateway = MCPToolGateway()

print("=== 测试股票查询 (中文名称) ===")
test_cases = [
    "上证指数",
    "贵州茅台",
    "茅台股价",
    "比亚迪",
    "深证成指",
]

for case in test_cases:
    print(f"\n查询: {case}")
    result = gateway.invoke("get_stock", {"target": case})
    if result.ok:
        print(f"✅ {result.text[:150]}...")
    else:
        print(f"❌ {result.error}: {result.text}")

print("\n\n=== 测试股票查询 (代码) ===")
code_cases = [
    "600519",
    "000001",
    "sh600036",
]

for case in code_cases:
    print(f"\n查询: {case}")
    result = gateway.invoke("get_stock", {"target": case})
    if result.ok:
        print(f"✅ {result.text[:150]}...")
    else:
        print(f"❌ {result.error}: {result.text}")
