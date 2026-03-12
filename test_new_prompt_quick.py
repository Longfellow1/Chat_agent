#!/usr/bin/env python3
"""
快速验证新提示词效果的测试脚本
测试关键场景：
1. 行程规划 vs 旅游知识查询
2. 股票行情 vs 股票知识查询
3. 纯闲聊识别
4. 附近查询
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

# 测试用例：(query, expected_tool, description)
TEST_CASES = [
    # 行程规划 vs 旅游知识查询
    ("我想去北京3天", "plan_trip", "行程规划：有目的地+天数"),
    ("帮我搜下去西藏旅游注意什么", "web_search", "旅游知识查询：有'搜'字"),
    ("上海2日游攻略帮我搜一下", "web_search", "旅游知识查询：有'搜'字"),
    ("国庆去哪里旅游好", "plan_trip", "行程规划：有旅游意图但无'搜'字"),
    
    # 股票行情 vs 股票知识查询
    ("茅台股价多少", "get_stock", "股票行情：公司名+股价"),
    ("A股今天怎么样", "web_search", "股票知识查询：指数查询"),
    ("比亚迪股票值得买吗", None, "投资建议：应该拒识"),
    
    # 纯闲聊
    ("我现在有点无聊，跟我玩成语接龙吧", None, "纯闲聊：无工具关键词"),
    ("你好", None, "纯闲聊：极短query"),
    
    # 附近查询
    ("附近有什么好吃的", "find_nearby", "附近查询：有'附近'+类别"),
    ("成都附近的酒店", "find_nearby", "附近查询：城市+类别"),
    
    # 天气查询
    ("北京天气怎么样", "get_weather", "天气查询：城市+天气"),
    ("明天要带伞吗", "get_weather", "天气查询：天气意图"),
    
    # 新闻查询
    ("最近有什么大事", "get_news", "新闻查询：新闻意图"),
]

def test_router():
    """测试路由器"""
    passed = 0
    failed = 0
    
    print("=" * 80)
    print("新提示词效果验证")
    print("=" * 80)
    
    for query, expected_tool, description in TEST_CASES:
        try:
            # 调用API
            response = requests.post(
                f"{BASE_URL}/chat",
                json={"query": query},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ {description}")
                print(f"   Query: {query}")
                print(f"   Error: HTTP {response.status_code}")
                failed += 1
                continue
            
            data = response.json()
            actual_tool = data.get("tool")
            
            # 检查结果
            if expected_tool is None:
                # 纯闲聊：tool应该是None或者LLM直接回复
                if actual_tool is None or actual_tool == "web_search":
                    print(f"✅ {description}")
                    print(f"   Query: {query}")
                    print(f"   Tool: {actual_tool} (纯闲聊)")
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
    
    # 总结
    print("=" * 80)
    print(f"总结: {passed} 通过, {failed} 失败")
    print(f"通过率: {passed}/{passed+failed} = {100*passed/(passed+failed):.1f}%")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = test_router()
    sys.exit(0 if success else 1)
