"""M5.4 plan_trip M4 端到端评测集（20条）

覆盖：
- 10个城市：上海/北京/杭州/成都/重庆/西安/南京/苏州/厦门/青岛
- 2种模式：公交/自驾
- 多种天数：1-5天
- 多种表达方式
"""

import sys
sys.path.insert(0, "agent_service")

from domain.intents.trip_router import route_trip_intent
from infra.tool_clients.mcp_gateway import MCPToolGateway


# 20条端到端测试用例
E2E_TEST_CASES = [
    # 上海（2条）
    ("帮我规划一个上海2日游", {"destination": "上海", "days": 2, "travel_mode": "transit"}),
    ("自驾上海3天怎么玩", {"destination": "上海", "days": 3, "travel_mode": "driving"}),
    
    # 北京（2条）
    ("北京3日游攻略", {"destination": "北京", "days": 3, "travel_mode": "transit"}),
    ("开车去北京玩4天", {"destination": "北京", "days": 4, "travel_mode": "driving"}),
    
    # 杭州（2条）
    ("杭州一日游", {"destination": "杭州", "days": 1, "travel_mode": "transit"}),
    ("自驾去杭州玩2天，有什么推荐", {"destination": "杭州", "days": 2, "travel_mode": "driving"}),
    
    # 成都（2条）
    ("成都2日游行程规划", {"destination": "成都", "days": 2, "travel_mode": "transit"}),
    ("驾车成都旅游3天", {"destination": "成都", "days": 3, "travel_mode": "driving"}),
    
    # 重庆（2条，特殊地形）
    ("重庆3日游", {"destination": "重庆", "days": 3, "travel_mode": "transit"}),
    ("自驾重庆4天行程", {"destination": "重庆", "days": 4, "travel_mode": "driving"}),
    
    # 西安（2条）
    ("西安旅游攻略3天", {"destination": "西安", "days": 3, "travel_mode": "transit"}),
    ("开车去西安玩2天", {"destination": "西安", "days": 2, "travel_mode": "driving"}),
    
    # 南京（2条）
    ("南京2日游怎么安排", {"destination": "南京", "days": 2, "travel_mode": "transit"}),
    ("自驾南京3天", {"destination": "南京", "days": 3, "travel_mode": "driving"}),
    
    # 苏州（2条）
    ("苏州一日游行程", {"destination": "苏州", "days": 1, "travel_mode": "transit"}),
    ("驾车苏州旅游2天", {"destination": "苏州", "days": 2, "travel_mode": "driving"}),
    
    # 厦门（2条）
    ("厦门3日游规划", {"destination": "厦门", "days": 3, "travel_mode": "transit"}),
    ("自驾厦门4天怎么玩", {"destination": "厦门", "days": 4, "travel_mode": "driving"}),
    
    # 青岛（2条）
    ("青岛2日游攻略", {"destination": "青岛", "days": 2, "travel_mode": "transit"}),
    ("开车去青岛玩3天", {"destination": "青岛", "days": 3, "travel_mode": "driving"}),
]


def test_e2e_20_cases():
    """端到端测试（20条完整覆盖）"""
    print("\n" + "=" * 80)
    print("M5.4 plan_trip M4 端到端评测（20条）")
    print("=" * 80)
    
    gateway = MCPToolGateway()
    success_count = 0
    transit_error_count = 0
    llm_rewrite_count = 0
    
    for i, (query, expected_params) in enumerate(E2E_TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/20] 查询: {query}")
        print(f"{'='*80}")
        
        # Step 1: Intent routing
        is_trip, params, reason = route_trip_intent(query)
        
        if not is_trip:
            print(f"❌ 意图路由失败: {reason}")
            continue
        
        # Verify params
        if params != expected_params:
            print(f"⚠️  参数不匹配")
            print(f"   期望: {expected_params}")
            print(f"   实际: {params}")
        
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
                    llm_rewrite_count += 1
                
                # Show output preview
                preview = result.text[:150] + "..." if len(result.text) > 150 else result.text
                print(f"\n输出预览: {preview}")
                
                success_count += 1
            else:
                print(f"❌ 工具调用失败: {result.error}")
        
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    # Summary
    success_rate = success_count / len(E2E_TEST_CASES) * 100
    print(f"\n{'='*80}")
    print(f"测试总结")
    print(f"{'='*80}")
    print(f"端到端成功率: {success_count}/{len(E2E_TEST_CASES)} ({success_rate:.1f}%)")
    print(f"交通时间错误: {transit_error_count}/{len(E2E_TEST_CASES)}")
    print(f"LLM重写成功: {llm_rewrite_count}/{len(E2E_TEST_CASES)}")
    print(f"{'='*80}")
    
    # Pass criteria: 100% success, 0 transit errors
    passed = success_rate == 100 and transit_error_count == 0
    print(f"\n总体结果: {'✅ 全部通过' if passed else '❌ 部分失败'}")
    
    return passed


def main():
    """运行M4端到端测试"""
    result = test_e2e_20_cases()
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
