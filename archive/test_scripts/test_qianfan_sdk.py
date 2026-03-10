#!/usr/bin/env python3
"""
使用百度千帆 SDK 测试 API Key
"""
import os
import qianfan

# 设置 API Key
API_KEY = "REDACTED"

# 方法 1: 直接设置环境变量
os.environ["QIANFAN_API_KEY"] = API_KEY

print("="*80)
print("测试 1: 使用 SDK 默认方式")
print("="*80)

try:
    # 创建 Chat Completion 对象
    chat_comp = qianfan.ChatCompletion()
    
    # 调用模型
    resp = chat_comp.do(
        model="ERNIE-Speed-128K",
        messages=[{"role": "user", "content": "你好"}]
    )
    
    print(f"✅ 成功!")
    print(f"Response: {resp}")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("测试 2: 显式传入 API Key")
print("="*80)

try:
    # 显式传入 API Key
    chat_comp = qianfan.ChatCompletion(api_key=API_KEY)
    
    resp = chat_comp.do(
        model="ERNIE-Speed-128K",
        messages=[{"role": "user", "content": "你好"}]
    )
    
    print(f"✅ 成功!")
    print(f"Response: {resp}")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("测试 3: 测试 web_search 插件")
print("="*80)

try:
    chat_comp = qianfan.ChatCompletion(api_key=API_KEY)
    
    resp = chat_comp.do(
        model="ERNIE-Speed-128K",
        messages=[{"role": "user", "content": "今天北京天气怎么样"}],
        plugins=["web_search"]
    )
    
    print(f"✅ 成功!")
    print(f"Response: {resp}")
    
    # 检查是否使用了插件
    if hasattr(resp, 'plugin_usage') or 'plugin_usage' in str(resp):
        print("\n✅ web_search 插件被调用!")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("测试完成")
print("="*80)
