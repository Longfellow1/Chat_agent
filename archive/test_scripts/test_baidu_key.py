#!/usr/bin/env python3
"""Test Baidu Qianfan API key."""

import requests
import json

# 提供的 Access Key
ACCESS_KEY = "REDACTED"

print("=" * 60)
print("测试百度千帆 API Key")
print("=" * 60)

# 测试1: 尝试直接使用 Access Key 调用 API
print("\n[测试1] 尝试使用 Access Key 调用文心一言 API...")

url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"

headers = {
    "Content-Type": "application/json",
}

payload = {
    "messages": [
        {
            "role": "user",
            "content": "特斯拉 Model 3 价格"
        }
    ],
    "enable_search": True,
    "search_type": "baidu_search",
}

params = {
    "access_token": ACCESS_KEY
}

try:
    response = requests.post(url, headers=headers, json=payload, params=params, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        if "result" in data:
            print(f"\n✅ 成功! AI 回答:\n{data['result'][:200]}...")
        else:
            print(f"\n⚠️  响应格式异常: {data}")
    else:
        print(f"\n❌ 失败: HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ 异常: {e}")

# 测试2: 尝试使用 BCE 签名方式
print("\n" + "=" * 60)
print("[测试2] 尝试使用 BCE 签名方式...")

# BCE Access Key 格式通常是: bce-v3/AK/SK
# 需要解析出 AK 和 SK
parts = ACCESS_KEY.split("/")
if len(parts) == 3 and parts[0] == "bce-v3":
    ak = parts[1]
    sk = parts[2]
    print(f"AK: {ak}")
    print(f"SK: {sk[:20]}...")
    
    # 尝试获取 Access Token
    print("\n尝试获取 Access Token...")
    token_url = "https://aip.baidubce.com/oauth/2.0/token"
    token_params = {
        "grant_type": "client_credentials",
        "client_id": ak,
        "client_secret": sk,
    }
    
    try:
        token_response = requests.post(token_url, params=token_params, timeout=10)
        print(f"状态码: {token_response.status_code}")
        print(f"响应: {token_response.text[:500]}")
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            if "access_token" in token_data:
                access_token = token_data["access_token"]
                print(f"\n✅ 成功获取 Access Token: {access_token[:30]}...")
                
                # 使用 Access Token 调用 API
                print("\n使用 Access Token 调用 AI 搜索...")
                params["access_token"] = access_token
                
                api_response = requests.post(url, headers=headers, json=payload, params=params, timeout=10)
                print(f"状态码: {api_response.status_code}")
                
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    if "result" in api_data:
                        print(f"\n✅ AI 搜索成功!")
                        print(f"回答: {api_data['result'][:300]}...")
                        
                        if "search_info" in api_data:
                            print(f"\n搜索信息:")
                            search_results = api_data["search_info"].get("search_results", [])
                            for i, r in enumerate(search_results[:3], 1):
                                print(f"  {i}. {r.get('title', 'N/A')}")
                                print(f"     {r.get('url', 'N/A')}")
                    else:
                        print(f"\n⚠️  响应格式异常: {api_data}")
                else:
                    print(f"\n❌ API 调用失败: {api_response.text[:500]}")
            else:
                print(f"\n❌ Token 响应中没有 access_token: {token_data}")
        else:
            print(f"\n❌ 获取 Token 失败: HTTP {token_response.status_code}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
else:
    print(f"❌ Access Key 格式不正确: {ACCESS_KEY}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
