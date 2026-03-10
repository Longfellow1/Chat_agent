"""Test AppBuilder API correctly."""
import json
import requests

# 你的 key
APPBUILDER_TOKEN = "REDACTED"

# 测试：列出可用的应用
url = "https://qianfan.baidubce.com/v2/app"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {APPBUILDER_TOKEN}",
}

print("=" * 60)
print("测试：获取应用列表")
print("=" * 60)

try:
    response = requests.get(url, headers=headers, timeout=5.0)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 成功!")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"✗ 失败:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"✗ 异常: {e}")
    import traceback
    traceback.print_exc()
