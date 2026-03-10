#!/usr/bin/env python3
"""
测试百度搜索组件 - 尝试使用 appbuilder SDK
"""
import os

os.environ["APPBUILDER_TOKEN"] = "REDACTED"

try:
    import appbuilder
    
    print("="*80)
    print("测试百度搜索组件 - appbuilder SDK")
    print("="*80)
    
    # 尝试使用 BaiduSearch 组件
    try:
        search = appbuilder.BaiduSearch()
        query = "特斯拉Model 3最新价格"
        print(f"\n查询: {query}\n")
        
        result = search.run(appbuilder.Message(query))
        print(f"✅ 成功!")
        print(f"\n结果:")
        print(result)
        
    except AttributeError as e:
        print(f"❌ BaiduSearch 组件不存在: {e}")
        print(f"\n可用组件:")
        # 列出所有可用组件
        for attr in dir(appbuilder):
            if not attr.startswith('_') and attr[0].isupper():
                print(f"  - {attr}")
                
except ImportError:
    print("❌ appbuilder SDK 未安装")
    print("安装命令: pip install appbuilder-sdk")
