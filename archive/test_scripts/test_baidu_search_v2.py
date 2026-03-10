#!/usr/bin/env python3
"""
测试百度千帆搜索组件 - 尝试不同的请求格式
"""
import requests
import json

API_KEY = "REDACTED"

url = "https://qianfan.baidubce.com/v2/components/baidu_search"
headers = {
    "Content-Type": "application/json",
    "X-Appbuilder-Authorization": f"Bearer {API_KEY}"
}

# 尝试 1: 使用 parameters 包装
print("="*80)
print("尝试 1: 使用 parameters 包装")
print("="*80)

data1 = {
    "version": "v1",
    "parameters": {
        "query": "今天北京天气怎么样",
        "top": 5
    },
    "stream": False
}

try:
    resp = requests.post(url, headers=headers, json=data1, timeout=30)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
    
    if resp.status_code == 200:
        print("\n✅ 成功!")
except Exception as e:
    print(f"Error: {e}")

# 尝试 2: 不同的参数名
print("\n" + "="*80)
print("尝试 2: 使用 input 包装")
print("="*80)

data2 = {
    "input": {
        "query": "今天北京天气怎么样"
    },
    "stream": False
}

try:
    resp = requests.post(url, headers=headers, json=data2, timeout=30)
    print(f"Status: {resp.status_code}")
    result = resp.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
    
    if resp.status_code == 200:
        print("\n✅ 成功!")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("测试完成")
print("="*80)
