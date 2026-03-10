# Bing MCP修复状态

## 修复内容
1. ✅ 添加market=zh-CN参数
2. ✅ 添加query预处理（但未生效）

## 验证结果

### 直接调用MCP（绕过服务）
```bash
query: "去西藏旅游需要注意什么"
market: "zh-CN"
结果: "进藏之前必看！西藏旅游注意事项（最全面，必收藏！）" ✅
```
market=zh-CN参数有效，返回完全相关的中文内容。

### 通过服务调用
```
宽松测试: 5/5 (100%) - 只检查tool_status=ok
严格测试: 1/5 (20%) - 检查内容相关性
```

4条失败都是LLM兜底："基于现有搜索结果未能找到相关信息"

## 问题分析

### 问题1: Query预处理未生效
```python
preprocess_web_search_query('帮我搜一下去西藏旅游需要注意什么')
# 返回: '帮我搜一下去西藏旅游需要注意什么' (未清洗)
```
停用词匹配逻辑有bug，"帮我搜一下"没被去掉。

### 问题2: 服务可能未重新加载
- 直接调用MCP: market=zh-CN生效 ✅
- 通过服务调用: 仍返回无关内容 ❌

可能原因：
1. uvicorn --reload未检测到代码变更
2. 代码有import缓存
3. 服务进程未重启

## 下一步

### 方案A: 重启服务验证
```bash
pkill -f uvicorn
PYTHONPATH=/Users/Harland/Documents/evaluation/agent_service python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
python tests/smoke/test_bing_mcp_strict.py
```

### 方案B: 修复query预处理
停用词匹配逻辑需要改进，但这不是核心问题。market=zh-CN才是关键。

### 方案C: 扩大测试集
从200条评测数据中筛选16条Bing MCP的case，作为完整smoke test。

## 评测通过标准（明确化）

### 当前标准（模糊）
- tool_provider = "bing_mcp" ✅
- tool_status = "ok" ✅
- fallback_chain = [] ✅

问题：LLM兜底也满足这些条件，但内容是编造的。

### 严格标准（推荐）
1. tool_provider = "bing_mcp" ✅
2. tool_status = "ok" ✅
3. fallback_chain = [] ✅
4. final_text包含query关键词 ✅
5. final_text不包含"基于现有搜索结果未能找到相关信息" ✅
6. final_text不包含明显无关内容（如"帮_百度百科"） ✅

### Golden Keywords标准
对于全量评测，需要为每条case定义golden_keywords：
- 宽松：包含query中的核心词即可（如"西藏"、"旅游"）
- 严格：必须包含具体信息（如"高原反应"、"边防证"）

建议：P0修复阶段使用严格标准，确保Bing真的返回了有效结果。
