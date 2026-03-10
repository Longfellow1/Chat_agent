"""End-to-end test for M5.4 plan_trip with REAL LLM post-processing."""

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
import json
from infra.tool_clients.amap_mcp_client import AmapMCPClient
from domain.trip.tool import plan_trip
from infra.llm_clients.lm_studio_client import LMStudioClient


async def test_plan_trip_with_real_llm():
    """Test plan_trip with REAL LLM post-processing."""
    
    print("=" * 80)
    print("M5.4 plan_trip 端到端测试 (含真实LLM后处理)")
    print("=" * 80)
    
    # Test queries
    queries = [
        "帮我规划一个上海2日游",
        "我想去北京玩两天，帮我安排一下",
        "自驾去杭州玩2天，有什么推荐"
    ]
    
    # Initialize clients
    amap_client = AmapMCPClient()
    llm_client = LMStudioClient()
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}/{len(queries)}: {query}")
        print(f"{'='*80}\n")
        
        # Extract parameters from query
        if "上海" in query:
            destination = "上海"
            travel_mode = "transit"
        elif "北京" in query:
            destination = "北京"
            travel_mode = "transit"
        elif "杭州" in query:
            destination = "杭州"
            travel_mode = "driving" if "自驾" in query else "transit"
        else:
            destination = "上海"
            travel_mode = "transit"
        
        print(f"📍 目的地: {destination}")
        print(f"🚗 出行方式: {'自驾' if travel_mode == 'driving' else '公共交通'}")
        print(f"\n{'─'*80}\n")
        
        # Step 1: Call plan_trip tool
        print("Step 1: 调用 plan_trip 工具...")
        result = await plan_trip(
            destination=destination,
            days=2,
            travel_mode=travel_mode,
            amap_client=amap_client
        )
        
        if not result.ok:
            print(f"❌ 工具调用失败: {result.error}")
            print(f"   {result.text}")
            continue
        
        print(f"✅ 工具调用成功")
        print(f"\n原始输出 (工具返回):")
        print(f"{'─'*80}")
        print(result.text[:500] + "..." if len(result.text) > 500 else result.text)
        print(f"{'─'*80}\n")
        
        # Step 2: REAL LLM post-processing
        print("Step 2: LLM 后处理 (真实LLM调用)...")
        
        try:
            # Build prompt for LLM
            system_prompt = """你是一个专业的旅游规划助手。你的任务是将结构化的行程信息重写为自然、友好、易读的文本。

要求：
1. 保持所有景点、地址、交通信息完整
2. 使用自然流畅的语言
3. 添加适当的过渡和连接词
4. 保持专业但友好的语气
5. 不要添加原文中没有的信息
6. 输出长度控制在800字以内
7. 直接输出重写后的文本，不要输出思考过程"""

            user_prompt = f"""用户查询: {query}

工具返回的原始行程信息:
{result.text}

请将上述行程信息重写为自然、友好的文本，让用户更容易理解和使用。"""

            # Call LLM
            print(f"   调用 LM Studio...")
            response = llm_client.generate(
                user_query=user_prompt,
                system_prompt=system_prompt
            )
            
            rewritten_text = response.strip()
            
            print(f"✅ LLM 后处理完成")
            print(f"\n最终输出 (LLM 重写后):")
            print(f"{'='*80}")
            print(rewritten_text)
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"❌ LLM 后处理失败: {e}")
            print(f"   使用原始输出")
            print(f"\n最终输出 (原始):")
            print(f"{'='*80}")
            print(result.text)
            print(f"{'='*80}\n")
        
        # Show raw data
        if result.raw:
            print(f"\n原始数据:")
            print(f"  Provider: {result.raw.get('provider')}")
            print(f"  Destination: {result.raw.get('destination')}")
            print(f"  Days: {result.raw.get('days')}")
            print(f"  Travel Mode: {result.raw.get('travel_mode')}")
            if 'itinerary' in result.raw:
                itinerary = result.raw['itinerary']
                print(f"  Itinerary Days: {len(itinerary.get('itinerary', []))}")
    
    # Cleanup
    amap_client.close()
    
    print(f"\n{'='*80}")
    print("测试完成！")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_plan_trip_with_real_llm())
