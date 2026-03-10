"""Test AppBuilder - try different endpoints."""
import json
import requests

TOKEN = "REDACTED"
APP_ID = "app-pQDPdqf4"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}

# 尝试直接运行对话（不创建会话）
url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
payload = {
    "app_id": APP_ID,
    "query": "什么是电动汽车",
    "stream": False,
}

print("测试：直接运行对话")
print("=" * 60)
response = requests.post(url, headers=headers, json=payload, timeout=10.0)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
