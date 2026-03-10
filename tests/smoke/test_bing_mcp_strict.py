#!/usr/bin/env python3
"""Bing MCP严格测试 - 检查返回内容相关性"""

import requests
import sys

BASE_URL = "http://localhost:8000"

# 测试case：query + 必须包含的关键词
TEST_CASES = [
    {
        "id": "H00006",
        "query": "帮我搜一下从北京去上海的攻略",
        "must_contain": ["北京", "上海", "攻略"],
        "must_not_contain": ["帮_百度百科", "帮的解释"],
    },
    {
        "id": "H00031",
        "query": "帮我搜一下去西藏旅游需要注意什么",
        "must_contain": ["西藏", "旅游", "注意"],
        "must_not_contain": ["帮_百度百科", "帮的解释", "帮（拼音"],
    },
    {
        "id": "H00033",
        "query": "帮我查下北京有什么好玩的地方推荐几个",
        "must_contain": ["北京", "好玩", "景点"],
        "must_not_contain": ["帮_百度百科", "查_百度百科"],
    },
    {
        "id": "H00055",
        "query": "成都旅游攻略有哪些",
        "must_contain": ["成都", "旅游", "攻略"],
        "must_not_contain": [],
    },
    {
        "id": "H00063",
        "query": "帮我查下二手车价格怎么样",
        "must_contain": ["二手车", "价格"],
        "must_not_contain": ["帮_百度百科", "查_百度百科"],
    },
]


def test_case(case):
    """测试单个case"""
    print(f"\n{'='*60}")
    print(f"测试 {case['id']}: {case['query']}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"query": case["query"]},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
        
        result = response.json()
        data = result.get("data", {})
        
        tool_provider = data.get("tool_provider", "")
        tool_status = data.get("tool_status", "fail")
        fallback_chain = data.get("fallback_chain", [])
        text = data.get("final_text", "")
        
        print(f"Provider: {tool_provider}")
        print(f"Status: {tool_status}")
        print(f"Fallback: {fallback_chain}")
        print(f"Text: {text[:200]}...")
        
        # 检查1: 不能走fallback
        if fallback_chain:
            print(f"❌ FAIL - 走了fallback链: {fallback_chain}")
            return False
        
        # 检查2: 必须包含关键词
        for keyword in case["must_contain"]:
            if keyword not in text:
                print(f"❌ FAIL - 缺少关键词: {keyword}")
                return False
        
        # 检查3: 不能包含无关内容
        for bad_keyword in case["must_not_contain"]:
            if bad_keyword in text:
                print(f"❌ FAIL - 包含无关内容: {bad_keyword}")
                return False
        
        # 检查4: 不能是LLM兜底
        if "基于现有搜索结果未能找到相关信息" in text:
            print(f"❌ FAIL - LLM兜底，Bing没返回有效结果")
            return False
        
        print(f"✅ PASS - 内容相关且完整")
        return True
        
    except requests.Timeout:
        print(f"❌ 超时")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def main():
    print("="*60)
    print("Bing MCP严格测试 - 内容相关性检查")
    print("="*60)
    
    # 检查服务
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ 服务未启动")
            sys.exit(1)
        print("✅ 服务正常")
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        sys.exit(1)
    
    # 运行测试
    results = []
    for case in TEST_CASES:
        result = test_case(case)
        results.append((case["id"], result))
    
    # 统计结果
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for case_id, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {case_id}")
    
    print(f"\n通过率: {passed}/{total} ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！Bing MCP返回内容完全相关！")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total-passed}条失败，Bing MCP仍返回无关内容")
        sys.exit(1)


if __name__ == "__main__":
    main()
