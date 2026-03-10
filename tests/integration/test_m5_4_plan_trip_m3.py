"""M5.4 plan_trip Milestone 3 端到端测试

测试从用户查询到最终输出的完整链路，包括：
1. 意图路由
2. 参数提取
3. 工具调用
4. LLM后处理
"""

import sys
import os
from pathlib import Path

# Load environment variables
env_file = Path('.env.agent')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key not in os.environ:
                    os.environ[key] = value

sys.path.insert(0, 'agent_service')

import asyncio
from domain.intents.trip_router import route_trip_intent, get_trip_routing_debug_info
from infra.tool_clients.mcp_gateway import MCPToolGateway


# Test cases
POSITIVE_CASES = [
    # Standard cases
    ("帮我规划一个上海2日游", {"destination": "上海", "days": 2, "travel_mode": "transit"}),
    ("我想去北京玩两天，帮我安排一下", {"destination": "北京", "days": 2, "travel_mode": "transit"}),
    ("自驾去杭州玩2天，有什么推荐", {"destination": "杭州", "days": 2, "travel_mode": "driving"}),
    ("上海有什么好玩的，帮我安排3天行程", {"destination": "上海", "days": 3, "travel_mode": "transit"}),
    ("开车去苏州玩一天", {"destination": "苏州", "days": 1, "travel_mode": "driving"}),
]

DRIVING_VS_TRANSIT_CASES = [
    ("上海2日游", {"destination": "上海", "days": 2, "travel_mode": "transit"}),
    ("自驾上海2日游", {"destination": "上海", "days": 2, "travel_mode": "driving"}),
    ("北京3天行程", {"destination": "北京", "days": 3, "travel_mode": "transit"}),
    ("开车去北京玩3天", {"destination": "北京", "days": 3, "travel_mode": "driving"}),
    ("杭州旅游攻略", {"destination": "杭州", "days": 2, "travel_mode": "transit"}),
    ("驾车杭州旅游", {"destination": "杭州", "days": 2, "travel_mode": "driving"}),
    ("苏州一日游", {"destination": "苏州", "days": 1, "travel_mode": "transit"}),
    ("自驾苏州一日游", {"destination": "苏州", "days": 1, "travel_mode": "driving"}),
    ("南京两天怎么玩", {"destination": "南京", "days": 2, "travel_mode": "transit"}),
    ("开车去南京玩两天", {"destination": "南京", "days": 2, "travel_mode": "driving"}),
]

NEGATIVE_CASES = [
    ("上海到北京怎么走", "导航意图"),
    ("上海有什么景点", "find_nearby意图"),
    ("上海天气怎么样", "get_weather意图"),
    ("上海附近的餐厅", "find_nearby意图"),
    ("上海最新新闻", "get_news意图"),
    ("帮我规划一下", "无目的地"),
    ("帮我规划一个行程", "无目的地"),
    ("打开行程规划", "操作指令"),
]


def test_intent_routing():
    """测试意图路由准确率"""
    print("=" * 80)
    print("测试1: 意图路由准确率")
    print("=" * 80)
    
    # Test positive cases
    positive_correct = 0
    for query, expected_params in POSITIVE_CASES + DRIVING_VS_TRANSIT_CASES:
        is_trip, params, reason = route_trip_intent(query)
        
        if is_trip and params.get("destination") == expected_params["destination"]:
            positive_correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {query}")
        print(f"   预期: {expected_params}")
        print(f"   实际: {params}")
        print(f"   原因: {reason}")
        print()
    
    # Test negative cases
    negative_correct = 0
    for query, reason in NEGATIVE_CASES:
        is_trip, params, routing_reason = route_trip_intent(query)
        
        if not is_trip:
            negative_correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {query} ({reason})")
        print(f"   应该拒绝，实际: is_trip={is_trip}")
        print(f"   原因: {routing_reason}")
        print()
    
    total_positive = len(POSITIVE_CASES) + len(DRIVING_VS_TRANSIT_CASES)
    total_negative = len(NEGATIVE_CASES)
    
    positive_rate = positive_correct / total_positive * 100
    negative_rate = negative_correct / total_negative * 100
    
    print(f"\n意图识别准确率: {positive_correct}/{total_positive} ({positive_rate:.1f}%)")
    print(f"负例拒绝率: {negative_correct}/{total_negative} ({negative_rate:.1f}%)")
    
    return positive_rate >= 90 and negative_rate == 100


def test_parameter_extraction():
    """测试参数提取准确率"""
    print("\n" + "=" * 80)
    print("测试2: 参数提取准确率")
    print("=" * 80)
    
    correct = 0
    total = 0
    
    for query, expected_params in POSITIVE_CASES + DRIVING_VS_TRANSIT_CASES:
        is_trip, params, reason = route_trip_intent(query)
        
        if not is_trip:
            continue
        
        total += 1
        
        # Check all parameters
        destination_match = params.get("destination") == expected_params["destination"]
        days_match = params.get("days") == expected_params["days"]
        mode_match = params.get("travel_mode") == expected_params["travel_mode"]
        
        if destination_match and days_match and mode_match:
            correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {query}")
        print(f"   预期: {expected_params}")
        print(f"   实际: {params}")
        print(f"   匹配: destination={destination_match}, days={days_match}, mode={mode_match}")
        print()
    
    accuracy = correct / total * 100 if total > 0 else 0
    print(f"\n参数提取准确率: {correct}/{total} ({accuracy:.1f}%)")
    
    return accuracy == 100


def test_end_to_end():
    """测试端到端流程（10个城市覆盖）"""
    print("\n" + "=" * 80)
    print("测试3: 端到端流程（10城市覆盖测试）")
    print("=" * 80)
    
    # 10 cases covering different cities and modes
    # 覆盖: 上海/北京/杭州/成都/重庆（特殊地形）+ 公交/自驾混合
    sample_cases = [
        ("帮我规划一个上海2日游", {"destination": "上海", "days": 2, "travel_mode": "transit"}),
        ("自驾上海2日游", {"destination": "上海", "days": 2, "travel_mode": "driving"}),
        ("北京3日游攻略", {"destination": "北京", "days": 3, "travel_mode": "transit"}),
        ("自驾去北京玩3天", {"destination": "北京", "days": 3, "travel_mode": "driving"}),
        ("自驾去杭州玩2天，有什么推荐", {"destination": "杭州", "days": 2, "travel_mode": "driving"}),
        ("杭州一日游", {"destination": "杭州", "days": 1, "travel_mode": "transit"}),
        ("成都2日游行程规划", {"destination": "成都", "days": 2, "travel_mode": "transit"}),
        ("开车去成都玩2天", {"destination": "成都", "days": 2, "travel_mode": "driving"}),
        ("重庆3日游", {"destination": "重庆", "days": 3, "travel_mode": "transit"}),  # 特殊地形城市
        ("驾车杭州旅游", {"destination": "杭州", "days": 2, "travel_mode": "driving"}),  # 修复后的case
    ]
    
    gateway = MCPToolGateway()
    success_count = 0
    transit_error_count = 0  # 交通时间错误计数
    
    for query, expected_params in sample_cases:
        print(f"\n{'='*80}")
        print(f"查询: {query}")
        print(f"{'='*80}\n")
        
        # Step 1: Intent routing
        is_trip, params, reason = route_trip_intent(query)
        
        if not is_trip:
            print(f"❌ 意图路由失败: {reason}")
            continue
        
        print(f"✅ 意图路由成功")
        print(f"   参数: {params}")
        
        # Step 2: Tool invocation
        try:
            result = gateway.invoke("plan_trip", params)
            
            if result.ok:
                print(f"✅ 工具调用成功")
                print(f"\n最终输出:")
                print(f"{'─'*80}")
                print(result.text[:300] + "..." if len(result.text) > 300 else result.text)
                print(f"{'─'*80}\n")
                
                # Check for error patterns (交通时间修复验证)
                if "高铁约3分钟" in result.text or "驾车约7分钟" in result.text:
                    print(f"⚠️  警告: 输出包含错误的交通时间")
                    transit_error_count += 1
                
                # Check for conservative estimates (应该看到"建议预留X分钟")
                if "建议预留" in result.text:
                    print(f"✅ 交通时间降级正确（使用保守估计）")
                
                success_count += 1
            else:
                print(f"❌ 工具调用失败: {result.error}")
                print(f"   {result.text}")
        
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    success_rate = success_count / len(sample_cases) * 100
    print(f"\n端到端成功率: {success_count}/{len(sample_cases)} ({success_rate:.1f}%)")
    print(f"交通时间错误: {transit_error_count}/{len(sample_cases)}")
    
    # 通过标准: 成功率100% 且 无交通时间错误
    return success_rate == 100 and transit_error_count == 0


def main():
    """运行所有测试"""
    print("M5.4 plan_trip Milestone 3 端到端测试\n")
    
    results = {
        "intent_routing": test_intent_routing(),
        "parameter_extraction": test_parameter_extraction(),
        "end_to_end": test_end_to_end(),
    }
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n总体结果: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
