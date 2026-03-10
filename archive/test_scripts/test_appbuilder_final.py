"""Test AppBuilder with correct app_id."""
import json
import requests

APPBUILDER_TOKEN = "REDACTED"
APP_ID = "app-pQDPdqf4"

print("=" * 60)
print("测试 AppBuilder API")
print("=" * 60)

# Step 1: 创建会话
url = "https://qianfan.baidubce.com/v2/app/conversation"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {APPBUILDER_TOKEN}",
}
payload = {"app_id": APP_ID}

print("\n1. 创建会话...")
response = requests.post(url, headers=headers, json=payload, timeout=5.0)
print(f"Status: {response.status_code}")

if response.status_code != 200:
    print(f"✗ 失败: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    exit(1)

data = response.json()
conversation_id = data.get("conversation_id")
print(f"✓ 会话ID: {conversation_id}")

# Step 2: 运行对话
url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
payload = {
    "app_id": APP_ID,
    "conversation_id": conversation_id,
    "query": "什么是电动汽车",
    "stream": False,
}

print("\n2. 运行对话...")
response = requests.post(url, headers=headers, json=payload, timeout=10.0)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✓ 成功!")
    print(f"\n回答:\n{data.get('answer', '')[:500]}")
    print(f"\n完整响应:\n{json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
else:
    print(f"✗ 失败: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
