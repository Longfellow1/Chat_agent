#!/usr/bin/env python3
"""
使用百度 RAGWithBaiduSearch 测试（带模型）
"""
import os
import appbuilder

# 设置 API Key
os.environ["APPBUILDER_TOKEN"] = "REDACTED"

print("="*80)
print("测试百度 RAGWithBaiduSearch")
print("="*80)

try:
    # 使用测试文件中的模型
    rag = appbuilder.RAGWithBaiduSearch(model="Qianfan-Agent-Speed-8K")
    
    query = "今天北京天气怎么样"
    msg = appbuilder.Message(query)
    
    print(f"\n查询: {query}")
    print(f"{'='*80}\n")
    
    result = rag(msg, stream=False)
    
    print(f"✅ 成功!")
    print(f"\nResult type: {type(result)}")
    print(f"Result.content: {result.content[:500] if result.content else 'None'}...")
    
    if hasattr(result, 'extra') and result.extra:
        print(f"\nResult.extra keys: {result.extra.keys() if isinstance(result.extra, dict) else type(result.extra)}")
        if isinstance(result.extra, dict):
            # 查找搜索结果
            for key in ['search_results', 'baidu_search', 'references', 'sources']:
                if key in result.extra:
                    print(f"\n找到搜索结果字段: {key}")
                    print(f"内容: {result.extra[key]}")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("测试完成")
print(f"{'='*80}")
