#!/usr/bin/env python3
"""
测试将 API Key 作为 bearer token 使用
"""
import os
import qianfan

API_KEY = "REDACTED"

print("="*80)
print("测试: 使用 bearer token")
print("="*80)

try:
    # 方法 1: 设置为 bearer token 环境变量
    os.environ["QIANFAN_BEARER_TOKEN"] = API_KEY
    
    chat_comp = qianfan.ChatCompletion()
    
    resp = chat_comp.do(
        model="ERNIE-Speed-128K",
        messages=[{"role": "user", "content": "你好"}]
    )
    
    print(f"✅ 成功!")
    print(f"Response: {resp}")
    
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("测试: 显式传入 bearer token")
print("="*80)

try:
    chat_comp = qianfan.ChatCompletion(bearer_token=API_KEY)
    
    resp = chat_comp.do(
        model="ERNIE-Speed-128K",
        messages=[{"role": "user", "content": "你好"}]
    )
    
    print(f"✅ 成功!")
    print(f"Response: {resp}")
    
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("测试: 尝试解析为 AK/SK")
print("="*80)

# 尝试解析格式
parts = API_KEY.split('/')
if len(parts) == 3:
    ak = parts[1]
    sk = parts[2]
    print(f"AK: {ak}")
    print(f"SK: {sk}")
    
    try:
        os.environ["QIANFAN_AK"] = ak
        os.environ["QIANFAN_SK"] = sk
        
        chat_comp = qianfan.ChatCompletion()
        
        resp = chat_comp.do(
            model="ERNIE-Speed-128K",
            messages=[{"role": "user", "content": "你好"}]
        )
        
        print(f"✅ 成功!")
        print(f"Response: {resp}")
        
    except Exception as e:
        print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("测试完成")
print("="*80)
