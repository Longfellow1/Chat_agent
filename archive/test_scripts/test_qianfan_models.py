#!/usr/bin/env python3
"""
测试不同的模型名称
"""
import requests
import json

API_KEY = "REDACTED"

url = "https://qianfan.baidubce.com/v2/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 尝试不同的模型名称
models = [
    "ERNIE-Speed-128K",
    "ERNIE-4.0-8K",
    "ERNIE-3.5-8K",
    "ERNIE-Lite-8K",
    "ERNIE-Speed",
    "ERNIE-Bot-4",
    "ERNIE-Bot",
    "ernie-speed-128k",
    "ernie_speed_128k",
    None  # 不指定模型
]

for model in models:
    print(f"\n{'='*70}")
    print(f"测试模型: {model if model else '(不指定)'}")
    print(f"{'='*70}")
    
    data = {
        "messages": [{"role": "user", "content": "你好"}]
    }
    if model:
        data["model"] = model
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {resp.status_code}")
        result = resp.json()
        
        if resp.status_code == 200:
            print(f"✅ 成功!")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:300]}")
            break  # 找到可用的模型就停止
        else:
            error_code = result.get('error', {}).get('code', 'unknown')
            error_msg = result.get('error', {}).get('message', 'unknown')
            print(f"❌ {error_code}: {error_msg}")
            
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*80)
print("测试完成")
print("="*80)
