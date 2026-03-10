#!/usr/bin/env python3
"""
测试百度 AI 搜索的 web_search 端点
这个端点应该返回纯搜索结果（references），不是 AI 总结
"""
import json
import urllib.request

API_KEY = "REDACTED"
BASE_URL = "https://qianfan.baidubce.com/v2/ai_search"

print("="*80)
print("测试百度 AI 搜索 - web_search 端点")
print("="*80)

query = "今天有哪些财经新闻"
print(f"\n查询: {query}")
print(f"{'='*80}\n")

# 构造请求
payload = {
    "query": query,
    "top": 5
}

try:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/web_search",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",  # 使用空格
        },
        method="POST",
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    
    print(f"✅ 成功!")
    print(f"\n完整响应:")
    print(json.dumps(body, indent=2, ensure_ascii=False))
    
    # 检查是否有 references
    if "references" in body:
        print(f"\n搜索结果 (references):")
        for i, ref in enumerate(body["references"], 1):
            print(f"\n{i}. {ref.get('title', 'N/A')}")
            print(f"   URL: {ref.get('url', 'N/A')}")
            print(f"   摘要: {ref.get('snippet', 'N/A')[:100]}")
    
except urllib.error.HTTPError as e:
    print(f"❌ HTTP 错误: {e.code}")
    print(f"响应: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("测试完成")
print(f"{'='*80}")
