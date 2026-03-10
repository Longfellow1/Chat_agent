#!/usr/bin/env python3
"""
使用百度 AppBuilder SDK 测试搜索组件
"""
import os
import appbuilder

# 1. 注入密钥
os.environ["APPBUILDER_TOKEN"] = "REDACTED"

print("="*80)
print("测试百度 AppBuilder SDK - BaiduSearch")
print("="*80)

try:
    # 2. 实例化搜索组件
    ai_search = appbuilder.AISearch()
    
    # 3. 执行搜索
    query = "今天北京天气怎么样"
    msg = appbuilder.Message(query)
    
    print(f"\n查询: {query}")
    print(f"{'='*80}\n")
    
    result = ai_search(msg, stream=False)
    
    # 4. 数据提取
    print(f"✅ 成功!")
    print(f"\nResult type: {type(result)}")
    print(f"Result.content type: {type(result.content)}")
    print(f"\nResult.content: {result.content}\n")
    
    # 解析搜索结果
    if isinstance(result.content, list):
        print(f"{'='*80}")
        print(f"搜索结果数量: {len(result.content)}")
        print(f"{'='*80}\n")
        
        for i, item in enumerate(result.content[:3], 1):
            print(f"结果 {i}:")
            if isinstance(item, dict):
                print(f"  标题: {item.get('title', 'N/A')}")
                print(f"  链接: {item.get('url', 'N/A')}")
                print(f"  描述: {item.get('description', 'N/A')[:100]}...")
            else:
                print(f"  {item}")
            print()
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print(f"{'='*80}")
print("测试完成")
print(f"{'='*80}")
