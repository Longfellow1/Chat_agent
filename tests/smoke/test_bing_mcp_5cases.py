#!/usr/bin/env python3
"""Bing MCP Smoke Test - 5条之前返回no_results的case"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

# 5条之前Bing返回no_results的case
TEST_CASES = [
    {
        "id": "H00006",
        "query": "帮我搜一下从北京去上海的攻略",
        "expected_tool": "web_search",
    },
    {
        "id": "H00031",
        "query": "帮我搜一下去西藏旅游需要注意什么",
        "expected_tool": "web_search",
    },
    {
        "id": "H00033",
        "query": "帮我查下北京有什么好玩的地方推荐几个",
        "expected_tool": "web_search",
    },
    {
        "id": "H00055",
        "query": "成都旅游攻略有哪些",
        "expected_tool": "web_search",
    },
    {
        "id": "H00063",
        "query": "帮我查下二手车价格怎么样",
        "expected_tool": "web_search",
    },
]


def test_single_case(case):
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
        
        # 正确解析返回结构
        data = result.get("data", {})
        tool_name = data.get("tool_name", "")
        tool_provider = data.get("tool_provider", "")
        tool_status = data.get("tool_status", "fail")
        fallback_chain = data.get("fallback_chain", [])
        text = data.get("final_text", "")[:200]
        
        print(f"工具: {tool_name}")
        print(f"Provider: {tool_provider}")
        print(f"状态: {tool_status}")
        print(f"兜底链: {fallback_chain}")
        print(f"返回文本: {text}...")
        
        # 判断是否成功
        if fallback_chain:
            print(f"⚠️  FALLBACK - Bing失败，兜底链接管: {fallback_chain}")
            return False
        elif tool_provider == "bing_mcp" and tool_status == "ok":
            print(f"✅ PASS - Bing MCP成功返回结果")
            return True
        elif "bing" in tool_provider.lower() and tool_status == "ok":
            print(f"✅ PASS - Bing相关provider成功")
            return True
        else:
            print(f"❌ FAIL - Provider: {tool_provider}, Status: {tool_status}")
            return False
            
    except requests.Timeout:
        print(f"❌ 超时")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def main():
    print("="*60)
    print("Bing MCP Smoke Test - 5条case")
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
        result = test_single_case(case)
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
        print("\n🎉 所有测试通过！Bing MCP修复成功！")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total-passed}条失败，Bing MCP仍有问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
