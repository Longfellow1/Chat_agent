"""测试 nearby 完整代码路径"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from app.factory import build_flow
from app.schemas.contracts import ChatRequest

print("=" * 60)
print("测试完整 nearby 代码路径")
print("=" * 60)

flow = build_flow()

# 测试1: 基础查询
query = "上海静安寺附近的咖啡厅"
print(f"\n查询: {query}")
print("-" * 60)

req = ChatRequest(query=query, session_id="test_path")
resp = flow.run(req)

print(f"Decision: {resp.decision_mode}")
print(f"Tool: {resp.tool_name}")
print(f"Tool Args: {resp.tool_args}")
print(f"Tool Status: {resp.tool_status}")
print(f"Tool Provider: {resp.tool_provider}")
print(f"Response: {resp.final_text[:200]}...")

# 检查是否使用了 LocationIntent
if resp.tool_args:
    print(f"\nTool Args 分析:")
    print(f"  - keyword: {resp.tool_args.get('keyword')}")
    print(f"  - city: {resp.tool_args.get('city')}")
    print(f"  - location: {resp.tool_args.get('location')}")

print("\n" + "=" * 60)
print("结论")
print("=" * 60)

checks = {
    "✅ 路由到 find_nearby": resp.tool_name == "find_nearby",
    "✅ 使用 amap_mcp provider": resp.tool_provider == "amap_mcp",
    "✅ 返回真实数据": "[mock-nearby]" not in resp.final_text,
    "✅ 提取了 location": resp.tool_args and resp.tool_args.get('location') is not None,
}

for check, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check}")

all_passed = all(checks.values())
print(f"\n{'✅ 所有检查通过' if all_passed else '❌ 部分检查失败'}")
