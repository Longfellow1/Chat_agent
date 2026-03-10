#!/usr/bin/env python
"""测试边界清洗修复 V2"""
import sys
from pathlib import Path

# 清除所有相关模块缓存
for mod in list(sys.modules.keys()):
    if 'domain.location' in mod:
        del sys.modules[mod]

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from domain.location.parser import parse_location_intent

test_cases = [
    ('我在天津天河，哪里有加油站', '天河'),
    ('我在厦门和平路，哪里有停车场', '和平路'),
    ('我在北京工业园，哪里有咖啡店', '工业园'),
    ('帮我找合肥天河周边的加油站', '天河'),
    ('我在广州五一广场，哪里有酒店', '五一广场'),
]

print("=" * 60)
print("边界清洗测试 V2")
print("=" * 60)

passed = 0
failed = 0

for query, expected_location in test_cases:
    intent = parse_location_intent(query)
    tool_args = intent.to_tool_args()
    actual_location = tool_args.get('location')
    
    is_correct = actual_location == expected_location
    status = "✅" if is_correct else "❌"
    
    if is_correct:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} {query}")
    print(f"   期望: {expected_location}, 实际: {actual_location}")

print()
print("=" * 60)
print(f"结果: {passed}/{len(test_cases)} 通过")
print("=" * 60)
