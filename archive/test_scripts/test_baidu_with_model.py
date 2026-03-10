import json
import requests

ACCESS_KEY = "REDACTED"

url = "https://qianfan.baidubce.com/v2/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_KEY}",
}

# 尝试常见的模型名称
models = [
    "ERNIE-Bot-4",
    "ERNIE-Speed",
    "ERNIE-Bot-turbo",
    "ERNIE-Bot",
]

for model in models:
    print(f"\n{'='*60}")
    print(f"测试模型: {model}")
    print('='*60)
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "什么是电动汽车"}
        ],
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5.0)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✓ 成功!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            break
        else:
            print(f"✗ 失败: {response.json()}")
    except Exception as e:
        print(f"✗ 异常: {e}")
