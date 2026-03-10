#!/usr/bin/env python3
"""
使用百度云 Access Key 获取 access_token
然后测试千帆 API
"""
import requests
import json
import re

# 解析 Access Key
ACCESS_KEY_FULL = "REDACTED"

# 尝试解析格式: bce-v3/ACCESS_KEY/SECRET_KEY
parts = ACCESS_KEY_FULL.split('/')
if len(parts) == 3:
    AK = parts[1]  # ALTAK-UmJvZh1PwHjLxdbsuGBDI
    SK = parts[2]  # 557a80a1055512ffedfe4b7611dc3922cbd4d200
    print(f"Access Key (AK): {AK}")
    print(f"Secret Key (SK): {SK}")
else:
    print(f"无法解析 Access Key 格式: {ACCESS_KEY_FULL}")
    exit(1)

# 步骤 1: 获取 access_token
print("\n" + "="*80)
print("步骤 1: 获取 access_token")
print("="*80)

token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={AK}&client_secret={SK}"
print(f"Token URL: {token_url}")

try:
    response = requests.post(token_url, timeout=10)
    print(f"Status: {response.status_code}")
    token_data = response.json()
    print(f"Response: {json.dumps(token_data, indent=2, ensure_ascii=False)}")
    
    if 'access_token' in token_data:
        access_token = token_data['access_token']
        print(f"\n✅ 成功获取 access_token: {access_token[:50]}...")
        
        # 步骤 2: 使用 access_token 调用千帆 API
        print("\n" + "="*80)
        print("步骤 2: 使用 access_token 调用千帆 API")
        print("="*80)
        
        # 测试 2.1: 简单对话
        print("\n--- 测试 2.1: 简单对话 (ERNIE-Speed) ---")
        chat_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-128k?access_token={access_token}"
        chat_data = {
            "messages": [{"role": "user", "content": "你好"}],
            "stream": False
        }
        response = requests.post(chat_url, json=chat_data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        # 测试 2.2: 带 web_search 插件的对话
        print("\n--- 测试 2.2: 带 web_search 插件 ---")
        plugin_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-128k?access_token={access_token}"
        plugin_data = {
            "messages": [{"role": "user", "content": "今天北京天气怎么样"}],
            "plugins": ["web_search"],
            "stream": False
        }
        response = requests.post(plugin_url, json=plugin_data, timeout=30)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 如果有 plugin_usage，说明插件被调用了
        if 'plugin_usage' in result:
            print("\n✅ web_search 插件被成功调用!")
            print(f"Plugin Usage: {json.dumps(result['plugin_usage'], indent=2, ensure_ascii=False)}")
        
    else:
        print(f"\n❌ 获取 access_token 失败")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("测试完成")
print("="*80)
