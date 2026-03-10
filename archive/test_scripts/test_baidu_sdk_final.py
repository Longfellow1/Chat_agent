#!/usr/bin/env python3
import os
import appbuilder

# 1. 注入正确的环境变量 Key
os.environ["APPBUILDER_TOKEN"] = "REDACTED"

# 2. 实例化搜索组件
baidu_search = appbuilder.BaiduSearch()

# 3. 构造请求参数
query = "今天国内有什么热点大事件？"
msg = appbuilder.Message(query)

# 4. 执行搜索并打印结果
try:
    print(f"正在使用 SDK 搜索: {query}")
    result = baidu_search(msg)
    print("搜索成功！前 3 条结果如下：")
    for i, item in enumerate(result.content[:3]):
        print(f"\n[{i+1}] {item.get('title')}")
        print(f"链接: {item.get('url')}")
        print(f"摘要: {item.get('description')}")
except Exception as e:
    print(f"SDK 调用失败: {e}")
    import traceback
    traceback.print_exc()
