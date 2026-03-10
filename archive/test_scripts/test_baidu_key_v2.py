#!/usr/bin/env python3
"""Test Baidu Qianfan API key - Version 2."""

import requests
import json

# 提供的 Key
PROVIDED_KEY = "REDACTED"

print("=" * 60)
print("测试百度千帆 API Key - 多种方式")
print("=" * 60)

# 解析 Key
parts = PROVIDED_KEY.split("/")
if len(parts) == 3:
    prefix = parts[0]
    ak = parts[1]
    sk = parts[2]
    
    print(f"\nKey 信息:")
    print(f"  前缀: {prefix}")
    print(f"  AK: {ak}")
    print(f"  SK: {sk[:30]}...")

# 测试1: 尝试千帆平台的 API Key 格式
print("\n" + "=" * 60)
print("[测试1] 尝试千帆平台 API Key 格式...")

# 千帆平台可能使用不同的 endpoint
qianfan_endpoints = [
    "https://aip.baidubce.com/oauth/2.0/token",
    "https://qianfan.baidubce.com/oauth/2.0/token",
]

for endpoint in qianfan_endpoints:
    print(f"\n尝试 endpoint: {endpoint}")
    
    token_params = {
        "grant_type": "client_credentials",
        "client_id": ak,
        "client_secret": sk,
    }
    
    try:
        response = requests.post(endpoint, params=token_params, timeout=10)
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print(f"  ✅ 成功获取 Token!")
                print(f"  Token: {data['access_token'][:40]}...")
                print(f"  过期时间: {data.get('expires_in', 'N/A')} 秒")
                
                # 保存 token 用于后续测试
                access_token = data["access_token"]
                break
            else:
                print(f"  ⚠️  响应: {data}")
        else:
            print(f"  ❌ 失败: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
else:
    print("\n❌ 所有 endpoint 都失败了")
    access_token = None

# 测试2: 如果获取到 token，测试 AI 搜索
if access_token:
    print("\n" + "=" * 60)
    print("[测试2] 测试 AI 搜索功能...")
    
    # 尝试不同的 API endpoint
    api_endpoints = [
        "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
        "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-4.0-8k",
        "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-3.5-8k",
    ]
    
    test_query = "特斯拉 Model 3 价格"
    
    for api_url in api_endpoints:
        print(f"\n尝试 API: {api_url.split('/')[-1]}")
        
        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": test_query
                }
            ],
            "enable_search": True,
        }
        
        params = {
            "access_token": access_token
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload, params=params, timeout=15)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    print(f"  ✅ 成功!")
                    print(f"  回答: {data['result'][:200]}...")
                    
                    if "search_info" in data:
                        print(f"\n  搜索结果:")
                        for i, r in enumerate(data["search_info"].get("search_results", [])[:3], 1):
                            print(f"    {i}. {r.get('title', 'N/A')}")
                    break
                else:
                    print(f"  ⚠️  响应: {data}")
            else:
                print(f"  ❌ 失败: {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ 异常: {e}")

# 测试3: 尝试百度搜索 API（如果有的话）
if access_token:
    print("\n" + "=" * 60)
    print("[测试3] 测试百度搜索 API...")
    
    search_url = "https://aip.baidubce.com/rpc/2.0/search/v1/search"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": "比亚迪汉 EV 续航",
        "num": 5,
    }
    
    params = {
        "access_token": access_token
    }
    
    try:
        response = requests.post(search_url, headers=headers, json=payload, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功!")
            print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
        else:
            print(f"❌ 失败: {response.text[:300]}")
    except Exception as e:
        print(f"❌ 异常: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

# 总结
print("\n总结:")
print(f"  提供的 Key: {PROVIDED_KEY}")
print(f"  AK: {ak}")
print(f"  SK: {sk[:20]}...")
print("\n建议:")
print("  1. 检查 Key 是否正确")
print("  2. 确认服务是否已开通")
print("  3. 检查 IP 白名单设置")
print("  4. 查看百度智能云控制台的错误日志")
