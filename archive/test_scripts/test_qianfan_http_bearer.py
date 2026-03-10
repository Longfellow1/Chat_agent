#!/usr/bin/env python3
"""
直接 HTTP 请求测试 Bearer token
"""
import requests
import json

API_KEY = "REDACTED"

print("="*80)
print("测试: Bearer token 格式")
print("="*80)

url = "https://qianfan.baidubce.com/v2/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
data = {
    "model": "ERNIE-Speed-128K",
    "messages": [{"role": "user", "content": "你好"}]
}

try:
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("测试: 不带 Bearer 前缀")
print("="*80)

headers2 = {
    "Content-Type": "application/json",
    "Authorization": API_KEY
}

try:
    resp = requests.post(url, headers=headers2, json=data, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("测试: X-Bce-Authorization header")
print("="*80)

headers3 = {
    "Content-Type": "application/json",
    "X-Bce-Authorization": API_KEY
}

try:
    resp = requests.post(url, headers=headers3, json=data, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("测试完成 - 这个 API Key 格式可能不正确")
print("="*80)
print("\n建议:")
print("1. 检查百度千帆控制台，确认 API Key 的正确格式")
print("2. 可能需要的是标准的 AK/SK（两个独立的字符串）")
print("3. 或者是一个纯字符串格式的 API Key（不带 bce-v3/ 前缀）")
