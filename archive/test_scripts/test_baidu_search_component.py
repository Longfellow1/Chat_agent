#!/usr/bin/env python3
"""
测试百度千帆 AppBuilder 搜索组件
正确的端点: /v2/components/baidu_search
"""
import requests
import json

API_KEY = "REDACTED"

print("="*80)
print("测试百度千帆搜索组件 (baidu_search)")
print("="*80)

url = "https://qianfan.baidubce.com/v2/components/baidu_search"
headers = {
    "Content-Type": "application/json",
    "X-Appbuilder-Authorization": f"Bearer {API_KEY}"
}
data = {
    "query": "今天北京天气怎么样",
    "top": 5,
    "stream": False
}

print(f"\nURL: {url}")
print(f"Headers: {json.dumps(headers, indent=2, ensure_ascii=False)}")
print(f"Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
print(f"\n{'='*80}")

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 成功!")
        print(f"\nResponse: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 解析搜索结果
        if 'results' in result:
            print(f"\n{'='*80}")
            print(f"搜索结果数量: {len(result['results'])}")
            print(f"{'='*80}")
            for i, item in enumerate(result['results'][:3], 1):
                print(f"\n结果 {i}:")
                print(f"  标题: {item.get('title', 'N/A')}")
                print(f"  链接: {item.get('url', 'N/A')}")
                print(f"  摘要: {item.get('snippet', 'N/A')[:100]}...")
    else:
        print(f"\n❌ 失败")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("测试完成")
print(f"{'='*80}")
