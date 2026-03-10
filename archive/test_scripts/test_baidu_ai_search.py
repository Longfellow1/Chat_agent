#!/usr/bin/env python3
"""
使用 OpenAI SDK 调用百度 AI 搜索
正确端点: /v2/ai_search/chat/completions
"""
from openai import OpenAI

API_KEY = "REDACTED"

print("="*80)
print("测试百度 AI 搜索 - OpenAI SDK")
print("="*80)

try:
    # 使用 OpenAI SDK，修改 base_url
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://qianfan.baidubce.com/v2/ai_search"
    )
    
    query = "今天有哪些财经新闻"
    print(f"\n查询: {query}")
    print(f"{'='*80}\n")
    
    response = client.chat.completions.create(
        model="ernie-3.5-8k",
        messages=[{"role": "user", "content": query}],
        stream=False
    )
    
    print(f"✅ 成功!")
    print(f"\n完整响应:")
    print(f"Response type: {type(response)}")
    print(f"Response: {response}")
    print(f"Response dict: {response.model_dump() if hasattr(response, 'model_dump') else 'N/A'}")
    
    if response.choices:
        print(f"\nAI 总结结果:")
        print(f"{response.choices[0].message.content}")
    else:
        print(f"\n⚠️ choices 为空")
    
    # 检查是否有搜索来源
    if hasattr(response, 'usage'):
        print(f"\nToken 使用: {response.usage}")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("测试完成")
print(f"{'='*80}")
