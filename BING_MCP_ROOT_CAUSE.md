# Bing MCP真实问题根因

## 问题现象
5条smoke test中，3条返回"基于现有搜索结果未能找到相关信息"：
- H00031: 帮我搜一下去西藏旅游需要注意什么
- H00033: 帮我查下北京有什么好玩的地方推荐几个  
- H00063: 帮我查下二手车价格怎么样

## 之前的错误判断
认为Bing MCP返回no_results，所以：
- 降低相关性阈值 0.1 → 0.05
- 添加保底逻辑：过滤后为空则使用原始结果
- 添加默认score=0.8

## 真实根因
**Bing MCP返回了完全不相关的垃圾结果**

实测"去西藏旅游需要注意什么"：
```
[Bing MCP] Got 5 results for query: 帮我搜一下去西藏旅游需要注意什么
[Bing MCP] All results filtered out, using raw results
Results: 5
First: {'title': '上海菜为啥又叫本帮菜？ - 知乎', 'url': 'https://www.zhihu.com/question/454442597', ...}
```

查询"西藏旅游注意事项"，Bing返回"上海菜为啥又叫本帮菜"！

## 问题链路
1. Bing MCP调用成功，返回5条结果
2. 但结果完全不相关（query: 西藏旅游，result: 上海菜）
3. `process_search_results`过滤后全部不相关
4. 触发保底逻辑：使用原始垃圾结果
5. 垃圾结果传给LLM
6. LLM判断"搜索结果未能找到相关信息"
7. 生成兜底回答
8. tool_status=ok, fallback_chain=[], 但内容是LLM兜底

## 为什么smoke test判PASS
- tool_provider = "bing_mcp" ✅
- tool_status = "ok" ✅
- fallback_chain = [] ✅
- 但final_text是LLM兜底生成的，不是Bing的真实结果

## 真正的问题
**Bing MCP的搜索质量有严重问题**，可能原因：
1. open-websearch MCP实现有bug
2. Bing API调用参数不对
3. 查询预处理有问题（"帮我搜一下"这种前缀影响搜索）
4. Bing本身对中文查询支持差

## 影响范围
16条Bing MCP的case中，可能大部分都是这个问题：
- 不是no_results（所以不走fallback_chain）
- 而是返回垃圾结果
- LLM看到垃圾后生成兜底回答
- 评测时如果golden_keywords宽松，可能误判PASS
- 如果golden_keywords要求具体信息，会FAIL

## 下一步
需要深入调试Bing MCP：
1. 直接调用open-websearch看原始返回
2. 检查是否需要query预处理（去掉"帮我搜一下"）
3. 对比Bing网页搜索结果vs MCP返回
4. 考虑换其他搜索provider（Tavily、DuckDuckGo）
