# Bing MCP问题最终结论

## 问题确认
Bing MCP返回垃圾结果（查"西藏旅游"返回"上海菜"），导致16条case失败。

## 修复尝试

### 1. 添加market=zh-CN参数 ❌
```python
"arguments": {
    "query": cleaned_query,
    "limit": 5,
    "engines": ["bing"],
    "market": "zh-CN"  # 已添加
}
```

**验证结果**:
- 直接调用MCP with market=zh-CN: 返回"进藏之前必看！西藏旅游注意事项" ✅
- 通过服务调用: 仍返回垃圾结果 ❌
- 日志确认参数已传递: `Request arguments: {'market': 'zh-CN'}` ✅

**结论**: open-websearch MCP接收到market参数但可能忽略了它。

### 2. 添加query预处理 ⚠️
```python
from domain.tools.query_preprocessor import preprocess_web_search_query
preprocessed = preprocess_web_search_query(query)
cleaned_query = preprocessed["normalized_query"]
```

**验证结果**:
- 日志显示: `Cleaned query: 帮我搜一下Python教程` (未清洗)
- preprocess_web_search_query()返回原样

**结论**: 停用词匹配逻辑有bug，"帮我搜一下"没被去掉。

## 根本原因

### 直接调用vs服务调用的差异
| 方式 | market参数 | 结果质量 |
|------|-----------|---------|
| 直接调用MCP | ✅ 生效 | ✅ 相关 |
| 通过服务调用 | ✅ 传递 | ❌ 垃圾 |

**可能原因**:
1. open-websearch MCP有bug，在某些情况下忽略market参数
2. 服务调用时有其他参数干扰（如query前缀）
3. MCP实例缓存导致参数未生效

## 当前状态

### 严格测试结果: 3/5 (60%)
- H00006 ✅ 北京到上海攻略
- H00031 ❌ 西藏旅游 → LLM兜底
- H00033 ❌ 北京好玩的地方 → LLM兜底  
- H00055 ✅ 成都旅游攻略
- H00063 ❌ 二手车价格 → LLM兜底

### 问题分类
1. **搜索质量问题** (H00031): Bing返回垃圾结果
2. **LLM兜底** (H00033, H00063): Bing返回结果但被过滤

## 建议方案

### 方案A: 修复query预处理（10分钟）
修复停用词匹配逻辑，确保"帮我搜一下"被去掉。这可能解决部分问题。

### 方案B: 降低相关性阈值（5分钟）
当前阈值0.05可能还是太高，导致有效结果被过滤。

### 方案C: 换provider（30分钟）
如果open-websearch MCP有bug，考虑换成Tavily或其他支持中文的provider。

### 方案D: 接受现状（0分钟）
60%通过率 + LLM兜底，实际用户体验可能可以接受。P0修复重点是城市提取(8条)已完成，Bing MCP(16条)可以降级为P1。

## 时间成本评估
- 继续调试Bing MCP: 不确定能否解决，可能需要1-2小时
- 城市提取已修复: 8/8 (100%)通过
- 总体P0进度: 8/24 (33%)完成

## 建议
先修复query预处理（方案A），如果仍不行则接受现状（方案D），将Bing MCP降级为P1，转测试前再决定是否换provider。
