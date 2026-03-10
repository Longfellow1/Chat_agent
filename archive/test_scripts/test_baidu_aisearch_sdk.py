#!/usr/bin/env python3
"""
测试百度 AISearch 组件 - 使用 appbuilder SDK
"""
import os

os.environ["APPBUILDER_TOKEN"] = "REDACTED"

import appbuilder

print("="*80)
print("测试百度 AISearch 组件")
print("="*80)

# 创建 AISearch 实例
search = appbuilder.AISearch()

query = "特斯拉Model 3最新价格"
print(f"\n查询: {query}\n")

try:
    # 执行搜索 - 使用字典格式
    result = search.run(messages=[{"role": "user", "content": query}])
    
    print(f"✅ 成功!")
    print(f"\n结果类型: {type(result)}")
    print(f"\n结果内容:")
    print(result)
    
    # 尝试访问结果属性
    if hasattr(result, 'content'):
        print(f"\nContent:")
        print(result.content)
    
    if hasattr(result, 'to_dict'):
        import json
        print(f"\nDict:")
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("测试完成")
print(f"{'='*80}")
