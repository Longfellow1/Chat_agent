# Bing MCP最终分析

## 测试结果
- 重启服务后严格测试：3/5 (60%)
- H00006 ✅ 北京到上海攻略
- H00031 ❌ 西藏旅游 → 返回"上海菜为啥又叫本帮菜"
- H00033 ❌ 北京好玩的地方 → LLM兜底
- H00055 ✅ 成都旅游攻略
- H00063 ❌ 二手车价格 → LLM兜底

## 问题确认

### 问题1: Query清洗未生效
```
[Bing MCP] Original query: 帮我搜一下去西藏旅游需要注意什么
[Bing MCP] Cleaned query: 帮我搜一下去西藏旅游需要注意什么
```
preprocess_web_search_query()返回原样，停用词匹配逻辑有bug。

### 问题2: market=zh-CN可能未生效
- 直接调用MCP with market=zh-CN: 返回"进藏之前必看！西藏旅游注意事项" ✅
- 通过服务调用: 返回"上海菜为啥又叫本帮菜" ❌

可能原因：
1. open-websearch MCP不支持market参数（被忽略）
2. 参数名不对（应该是mkt而不是market）
3. 需要通过环境变量设置

## 验证market参数

### 测试1: 检查open-websearch文档
需要查看open-websearch的参数列表，确认是否支持market/mkt参数。

### 测试2: 尝试不同参数名
```python
# 尝试1: market
"arguments": {"query": "...", "market": "zh-CN"}

# 尝试2: mkt
"arguments": {"query": "...", "mkt": "zh-CN"}

# 尝试3: locale
"arguments": {"query": "...", "locale": "zh-CN"}

# 尝试4: 环境变量
env={"BING_MARKET": "zh-CN", ...}
```

## 当前状态

### 有效的修复
1. ✅ 添加market=zh-CN参数（代码已添加，但可能未生效）
2. ⚠️ 添加query预处理（代码已添加，但逻辑有bug）

### 待验证
1. open-websearch是否支持market参数
2. 参数名是否正确
3. 是否需要通过环境变量设置

### 待修复
1. query预处理逻辑（停用词匹配bug）
2. 如果open-websearch不支持market，考虑换provider（Tavily、DuckDuckGo）

## 下一步行动

### 方案A: 验证market参数（5分钟）
直接测试不同参数名，看哪个生效。

### 方案B: 修复query预处理（10分钟）
修复停用词匹配逻辑，确保"帮我搜一下"被去掉。

### 方案C: 换provider（30分钟）
如果open-websearch不支持market，换成Tavily或其他支持中文的provider。

## 建议
先执行方案A验证market参数，如果不支持则考虑方案C。方案B（query清洗）是辅助优化，不是核心问题。
