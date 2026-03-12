#!/usr/bin/env python3
"""端到端测试新提示词效果"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 测试用例
test_cases = [
    ("我想去北京3天", "plan_trip", "行程规划"),
    ("我现在有点无聊，跟我玩成语接龙吧", None, "纯闲聊"),
    ("北京天气怎么样", "get_weather", "天气查询"),
    ("附近有什么好吃的", "find_nearby", "附近查询"),
]

print("=" * 80)
print("端到端测试：新提示词效果验证")
print("=" * 80)

passed = 0
failed = 0

for query, expected_tool, description in test_cases:
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"query": query},
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"❌ {description}")
            print(f"   Query: {query}")
            print(f"   Error: HTTP {response.status_code}")
            failed += 1
            continue
        
        data = response.json()
        actual_tool = data.get("tool_name")
        
        # 检查结果
        if expected_tool is None:
            # 纯闲聊：tool应该是None或者decision_mode是reply
            if actual_tool is None or data.get("decision_mode") == "reply":
                print(f"✅ {description}")
                print(f"   Query: {query}")
                print(f"   Tool: {actual_tool}, Mode: {data.get('decision_mode')}")
                passed += 1
            else:
                print(f"❌ {description}")
                print(f"   Query: {query}")
                print(f"   Expected: None (纯闲聊), Got: {actual_tool}")
                failed += 1
        else:
            # 工具调用
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
    
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Query: {query}")
        print(f"   Error: {str(e)}")
        failed += 1
    
    print()
    time.sleep(0.5)  # 避免请求过快

# 总结
print("=" * 80)
print(f"总结: {passed} 通过, {failed} 失败")
print(f"通过率: {passed}/{passed+failed} = {100*passed/(passed+failed):.1f}%")
print("=" * 80)
