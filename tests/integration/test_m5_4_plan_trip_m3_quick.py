"""M5.4 plan_trip M3 快速验证测试

验证两个关键修复：
1. "驾车杭州旅游"信号词修复
2. 端到端测试扩充（快速版本，只测试5个城市）
"""

import sys
sys.path.insert(0, "agent_service")

from domain.intents.trip_router import route_trip_intent
from infra.tool_clients.mcp_gateway import MCPToolGateway


def test_driving_city_travel_fix():
    """测试"驾车+城市+旅游"信号词修复"""
    print("\n" + "=" * 80)
    print("测试1: 驾车+城市+旅游 信号词修复")
    print("=" * 80)
    
    test_cases = [
        ("驾车杭州旅游", True, {"destination": "杭州", "days": 2, "travel_mode": "driving"}),
        ("自驾上海旅游", True, {"destination": "上海", "days": 2, "travel_mode": "driving"}),
        ("开车去北京玩", True, {"destination": "北京", "days": 2, "travel_mode": "driving"}),
    ]
    
    passed = 0
    for query, should_match, expected_params in test_cases:
        is_trip, params, reason = route_trip_intent(query)
        
        if is_trip == should_match:
            if is_trip and params == expected_params:
                print(f"✅ {query}: 识别成功，参数正确")
                passed += 1
            elif is_trip:
                print(f"⚠️  {query}: 识别成功，但参数不匹配")
                print(f"   期望: {expected_params}")
                print(f"   实际: {params}")
            else:
                print(f"✅ {query}: 正确拒绝")
                passed += 1
        else:
            print(f"❌ {query}: 识别失败")
            print(f"   原因: {reason}")
    
    print(f"\n通过率: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.1f}%)")
    return passed == len(test_cases)


def test_end_to_end_quick():
    """快速端到端测试（5个城市）"""
    print("\n" + "=" * 80)
    print("测试2: 端到端快速验证（5城市）")
    print("=" * 80)
    
    # 5个城市覆盖：上海/北京/杭州/成都/重庆（特殊地形）
    sample_cases = [
        ("帮我规划一个上海2日游", {"destination": "上海", "days": 2, "travel_mode": "transit"}),
        ("北京3日游攻略", {"destination": "北京", "days": 3, "travel_mode": "transit"}),
        ("自驾去杭州玩2天", {"destination": "杭州", "days": 2, "travel_mode": "driving"}),
        ("成都2日游行程规划", {"destination": "成都", "days": 2, "travel_mode": "transit"}),
        ("重庆3日游", {"destination": "重庆", "days": 3, "travel_mode": "transit"}),  # 特殊地形
    ]
    
    gateway = MCPToolGateway()
    success_count = 0
    transit_error_count = 0
    
    for query, expected_params in sample_cases:
        print(f"\n{'='*80}")
        print(f"查询: {query}")
        print(f"{'='*80}")
        
        # Step 1: Intent routing
        is_trip, params, reason = route_trip_intent(query)
        
        if not is_trip:
            print(f"❌ 意图路由失败: {reason}")
            continue
        
        print(f"✅ 意图路由成功: {params}")
        
        # Step 2: Tool invocation
        try:
            result = gateway.invoke("plan_trip", params)
            
            if result.ok:
                print(f"✅ 工具调用成功")
                
                # Check for error patterns
                if "高铁约3分钟" in result.text or "驾车约7分钟" in result.text:
                    print(f"❌ 交通时间错误")
                    transit_error_count += 1
                elif "建议预留" in result.text:
                    print(f"✅ 交通时间降级正确")
                
                # Check LLM rewrite
                if result.raw and result.raw.get("llm_rewritten"):
                    print(f"✅ LLM重写成功")
                
                success_count += 1
            else:
                print(f"❌ 工具调用失败: {result.error}")
        
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    success_rate = success_count / len(sample_cases) * 100
    print(f"\n{'='*80}")
    print(f"端到端成功率: {success_count}/{len(sample_cases)} ({success_rate:.1f}%)")
    print(f"交通时间错误: {transit_error_count}/{len(sample_cases)}")
    print(f"{'='*80}")
    
    return success_rate == 100 and transit_error_count == 0


def main():
    """运行快速验证测试"""
    print("M5.4 plan_trip M3 快速验证测试\n")
    
    results = {
        "driving_city_travel_fix": test_driving_city_travel_fix(),
        "end_to_end_quick": test_end_to_end_quick(),
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
