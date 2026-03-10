#!/usr/bin/env python3
"""
测试百度千帆 API Key
尝试不同的 API 端点和参数组合
"""
import requests
import json

API_KEY = "REDACTED"

def test_endpoint(name, url, headers, data):
    """测试一个 API 端点"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

# 测试 1: Plugin API (根据文档链接推测)
print("\n" + "="*80)
print("测试 1: Plugin API - web_search 插件")
print("="*80)
test_endpoint(
    "Plugin API with web_search",
    "https://qianfan.baidubce.com/v2/app/conversation/plugins",
    {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    },
    {
        "plugins": ["web_search"],
        "query": "今天天气怎么样",
        "stream": False
    }
)

# 测试 2: Chat Completions with tools
print("\n" + "="*80)
print("测试 2: Chat Completions with tools")
print("="*80)
test_endpoint(
    "Chat Completions with web_search tool",
    "https://qianfan.baidubce.com/v2/chat/completions",
    {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    },
    {
        "model": "ERNIE-Speed",
        "messages": [{"role": "user", "content": "今天天气怎么样"}],
        "tools": [{"type": "web_search"}],
        "stream": False
    }
)

# 测试 3: 简单的 Chat Completions
print("\n" + "="*80)
print("测试 3: 简单的 Chat Completions")
print("="*80)
test_endpoint(
    "Simple Chat Completions",
    "https://qianfan.baidubce.com/v2/chat/completions",
    {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    },
    {
        "model": "ERNIE-Speed",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }
)

# 测试 4: 尝试不同的 Authorization 格式
print("\n" + "="*80)
print("测试 4: 不同的 Authorization 格式")
print("="*80)
test_endpoint(
    "Authorization without Bearer",
    "https://qianfan.baidubce.com/v2/chat/completions",
    {
        "Content-Type": "application/json",
        "Authorization": API_KEY
    },
    {
        "model": "ERNIE-Speed",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }
)

# 测试 5: 尝试 X-Bce-Authorization header
print("\n" + "="*80)
print("测试 5: X-Bce-Authorization header")
print("="*80)
test_endpoint(
    "X-Bce-Authorization",
    "https://qianfan.baidubce.com/v2/chat/completions",
    {
        "Content-Type": "application/json",
        "X-Bce-Authorization": API_KEY
    },
    {
        "model": "ERNIE-Speed",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }
)

print("\n" + "="*80)
print("测试完成")
print("="*80)
