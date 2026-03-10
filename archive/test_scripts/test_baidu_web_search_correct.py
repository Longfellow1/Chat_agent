#!/usr/bin/env python3
"""
测试百度搜索组件的正确端点：/v2/ai_search/web_search
返回 references[] 列表，含 title/snippet/url
"""
import json
import urllib.request

API_KEY = "REDACTED"
BASE_URL = "https://qianfan.baidubce.com/v2/ai_search"

print("="*80)
print("测试百度搜索组件 - /v2/ai_search/web_search 端点")
print("="*80)

query = "特斯拉Model 3最新价格"
print(f"\n查询: {query}")
print(f"{'='*80}\n")

# 构造请求 - 尝试不同的参数名
payload = {
    "query": query
}

try:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/web_search",
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Appbuilder-Authorization": f"Bearer {API_KEY}",
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
            print(f"   摘要: {ref.get('snippet', ref.get('content', 'N/A'))[:150]}")
    
except urllib.error.HTTPError as e:
    print(f"❌ HTTP 错误: {e.code}")
    error_body = e.read().decode('utf-8')
    print(f"响应: {error_body}")
    try:
        error_json = json.loads(error_body)
        print(f"\n错误详情:")
        print(json.dumps(error_json, indent=2, ensure_ascii=False))
    except:
        pass
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("测试完成")
print(f"{'='*80}")
