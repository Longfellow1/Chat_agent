#!/usr/bin/env python3
"""快速测试排除法修复"""

import sys
sys.path.insert(0, '/Users/Harland/agent_service')

from agent_service.domain.intents.router_4b_with_logprobs import RuleBasedRouter

# 测试用例
test_cases = [
    ("我想去北京3天", "plan_trip", "应该匹配规则1：目的地+时间"),
    ("我现在有点无聊，跟我玩成语接龙吧", None, "应该返回None：纯闲聊"),
    ("你好", None, "应该返回None：纯闲聊"),
    ("北京天气怎么样", "get_weather", "应该匹配规则3：天气关键词"),
    ("附近有什么好吃的", "find_nearby", "应该匹配规则2：位置+类别"),
]

print("=" * 80)
print("排除法修复验证")
print("=" * 80)

passed = 0
failed = 0

for query, expected_tool, description in test_cases:
    result = RuleBasedRouter.try_route(query)
    actual_tool = result.tool.value if result else None
    
    if actual_tool == expected_tool:
        print(f"✅ {description}")
        print(f"   Query: {query}")
        print(f"   Tool: {actual_tool}")
        passed += 1
    else:
        print(f"❌ {description}")
        print(f"   Query: {query}")
        print(f"   Expected: {expected_tool}, Got: {actual_tool}")
        failed += 1
    print()

print("=" * 80)
print(f"总结: {passed} 通过, {failed} 失败")
print("=" * 80)

sys.exit(0 if failed == 0 else 1)
