#!/usr/bin/env python3
"""Test Baidu MCP tools."""

import requests
import json

# BCE Access Key
ACCESS_KEY = "REDACTED"

print("=" * 60)
print("测试百度 MCP 工具")
print("=" * 60)

# MCP 工具调用的基础 URL
MCP_BASE_URL = "https://qianfan.baidubce.com/v2/app/conversation/runs"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_KEY}",
}

# 测试1: 百度搜索 MCP
print("\n[测试1] 百度搜索 MCP - 特斯拉 Model 3 价格")

payload = {
    "app_id": "mcp_baidu_web_search",  # 百度搜索 MCP 工具
    "query": "特斯拉 Model 3 价格",
    "stream": False,
}

try:
    response = requests.post(MCP_BASE_URL, headers=headers, json=payload, timeout=15)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ 成功!")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
    else:
        print(f"\n❌ 失败")
except Exception as e:
    print(f"❌ 异常: {e}")

# 测试2: 百度百科 MCP
print("\n" + "=" * 60)
print("[测试2] 百度百科 MCP - 电动汽车")

payload = {
    "app_id": "baidu_baike",  # 百度百科 MCP 工具
    "query": "电动汽车",
    "stream": False,
}

try:
    response = requests.post(MCP_BASE_URL, headers=headers, json=payload, timeout=15)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ 成功!")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
    else:
        print(f"\n❌ 失败")
except Exception as e:
    print(f"❌ 异常: {e}")

# 测试3: 尝试直接调用 MCP 工具 API
print("\n" + "=" * 60)
print("[测试3] 尝试直接调用 MCP 工具 API")

# 百度搜索工具的直接 API
search_url = "https://qianfan.baidubce.com/v2/tools/mcp_baidu_web_search"

payload = {
    "query": "比亚迪汉 EV 续航",
}

try:
    response = requests.post(search_url, headers=headers, json=payload, timeout=15)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ 成功!")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
    else:
        print(f"\n❌ 失败")
except Exception as e:
    print(f"❌ 异常: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
