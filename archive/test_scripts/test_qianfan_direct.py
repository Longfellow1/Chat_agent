#!/usr/bin/env python3
"""
直接测试百度千帆 API Key
尝试所有可能的端点和格式
"""
import requests
import json

API_KEY = "REDACTED"

def test(name, url, headers, data=None, method="POST"):
    print(f"\n{'='*70}")
    print(f"测试: {name}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    try:
        if method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            resp = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        try:
            print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:500]}")
        except:
            print(f"Response: {resp.text[:500]}")
        return resp
    except Exception as e:
        print(f"Error: {e}")
        return None

# 测试 1: 千帆 v2 API - 直接用 API Key
print("\n" + "="*80)
print("千帆 v2 API 测试")
print("="*80)

test("v2 chat - Authorization header",
     "https://qianfan.baidubce.com/v2/chat/completions",
     {"Content-Type": "application/json", "Authorization": API_KEY},
     {"model": "ERNIE-Speed-128K", "messages": [{"role": "user", "content": "你好"}]})

test("v2 chat - X-Bce-Date header",
     "https://qianfan.baidubce.com/v2/chat/completions",
     {"Content-Type": "application/json", "Authorization": API_KEY, "X-Bce-Date": "2024-01-01T00:00:00Z"},
     {"model": "ERNIE-Speed-128K", "messages": [{"role": "user", "content": "你好"}]})

# 测试 2: 列出可用模型
test("v2 models list",
     "https://qianfan.baidubce.com/v2/models",
     {"Authorization": API_KEY},
     method="GET")

# 测试 3: 尝试不同的模型名称
models_to_try = [
    "ERNIE-Speed-128K",
    "ERNIE-4.0-8K",
    "ERNIE-3.5-8K",
    "ERNIE-Lite-8K",
    "ernie-speed-128k",
    "ernie_speed_128k"
]

for model in models_to_try:
    test(f"Model: {model}",
         "https://qianfan.baidubce.com/v2/chat/completions",
         {"Content-Type": "application/json", "Authorization": API_KEY},
         {"model": model, "messages": [{"role": "user", "content": "你好"}]})

# 测试 4: 旧版 API (rpc 格式)
print("\n" + "="*80)
print("旧版 RPC API 测试")
print("="*80)

# 需要先获取 access_token
# 但我们的 Key 格式不是标准的 AK/SK，跳过

print("\n" + "="*80)
print("测试完成")
print("="*80)
