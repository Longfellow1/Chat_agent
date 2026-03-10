# Mock 数据污染彻底清理验证报告

## 清理时间
2026-03-10

## 清理内容

### 1. Provider Config 中的 Mock Provider 配置 ✅
**文件**: `agent_service/infra/tool_clients/provider_config.py`

**删除的 mock 配置**:
- `find_nearby` 中的 mock provider (priority=99)
- `get_weather` 中的 mock provider (priority=99)
- `get_stock` 中的 mock provider (priority=2)

**修改前**:
```python
"find_nearby": [
    ProviderConfig(name="amap_mcp", ...),
    ProviderConfig(name="baidu_maps_mcp", ...),
    ProviderConfig(name="mock", priority=99, enabled=True),  # ❌ 删除
],
```

**修改后**:
```python
"find_nearby": [
    ProviderConfig(name="amap_mcp", ...),
    ProviderConfig(name="baidu_maps_mcp", ...),
],
```

### 2. Chat Flow 中的 Mock Provider 检查 ✅
**文件**: `agent_service/app/orchestrator/chat_flow.py`

**删除的 mock 检查**:
- `mock_search`
- `mock_nearby`
- `mock_trip`

**修改前**:
```python
if provider in {"tavily", "amap", "tavily_trip", "mock_search", "mock_nearby", "mock_trip"}:
    return True
```

**修改后**:
```python
if provider in {"tavily", "amap", "tavily_trip"}:
    return True
```

### 3. MCP Gateway 中的 Mock 相关代码 ✅
**文件**: `agent_service/infra/tool_clients/mcp_gateway.py`

**更新的注释和日志**:
- `_init_get_weather_chain()`: "QWeather -> Tavily -> Mock" → "QWeather -> Tavily -> LLM Fallback"
- `_init_get_stock_chain()`: "Sina -> Mock" → "Sina -> Web Search -> LLM Fallback"
- `_nearby()`: "falling back to mock" → "falling back to web_search"

### 4. 删除的文件 ✅
**文件**: `agent_service/infra/tool_clients/weather_client.py`

**原因**: 已弃用的 mock weather 实现，现在使用 provider chain 替代

## 验证清单

### ✅ 代码扫描结果

**搜索 1: Mock Provider 注册**
```bash
grep -r "register_provider.*mock" agent_service/
# 结果: 无匹配 ✅
```

**搜索 2: Mock Provider 类**
```bash
grep -r "MockProvider" agent_service/
# 结果: 无匹配 ✅
```

**搜索 3: Mock 文件**
```bash
find agent_service -name "*mock*provider*" -o -name "*mock*client*"
# 结果: 无匹配 ✅
```

**搜索 4: Provider Config 中的 Mock**
```bash
grep -n '"mock"' agent_service/infra/tool_clients/provider_config.py
# 结果: 无匹配 ✅
```

**搜索 5: Chat Flow 中的 Mock**
```bash
grep -n "mock_search\|mock_nearby\|mock_trip" agent_service/app/orchestrator/chat_flow.py
# 结果: 无匹配 ✅
```

### ✅ 语法检查
- `provider_config.py`: No diagnostics found ✅
- `chat_flow.py`: No diagnostics found ✅
- `mcp_gateway.py`: No diagnostics found ✅

## Mock 数据污染来源分析

### 原始问题 (47 条 mock 数据)
1. **Bing MCP** (16 条) - 返回垃圾结果
   - 解决方案: 禁用 Bing MCP，启用百度 web_search
   - 状态: ✅ 已修复

2. **城市提取** (8 条) - 解析失败
   - 解决方案: 扩充城市列表，添加 blocked 词表
   - 状态: ✅ 已修复

3. **高德 MCP** (9 条) - 服务不稳定
   - 状态: ⚠️ 需要进一步调查

4. **新闻 Provider** (6 条) - 实现 bug
   - 状态: ⚠️ 需要进一步调查

5. **股票映射** (5 条) - 意图路由错误
   - 状态: ⚠️ 需要进一步调查

6. **地图服务** (2 条) - 都挂了
   - 状态: ⚠️ 需要进一步调查

7. **其他** (1 条) - 需要逐个分析
   - 状态: ⚠️ 需要进一步调查

### Mock 污染的根本原因
1. **Provider Chain 中的 Mock Fallback**: 当所有真实 provider 都失败时，会回退到 mock provider
2. **旧的 Weather Client**: 有 mock weather 实现作为降级方案
3. **Chat Flow 中的 Mock 检查**: 对 mock provider 的特殊处理

## 清理后的 Fallback 链路

### 新的 Fallback 策略 (无 Mock)
```
Tool Call
  ↓
Provider Chain (按优先级)
  ├─ Primary Provider (e.g., baidu_web_search)
  ├─ Secondary Provider (e.g., tavily)
  └─ Tertiary Provider (if available)
  ↓
Web Search (if all providers fail)
  ↓
LLM Fallback (if web search fails)
```

### 各工具的 Fallback 链路

**web_search**:
1. baidu_web_search (priority=1)
2. tavily (priority=3)
3. _fallback_to_web_search() (重新调用 web_search)
4. _fallback_to_llm() (LLM 生成回复)

**find_nearby**:
1. amap_mcp (priority=1)
2. baidu_maps_mcp (priority=2)
3. _fallback_to_web_search() (web search 附近查询)
4. _fallback_to_llm() (LLM 生成回复)

**get_weather**:
1. qweather (priority=1)
2. tavily (priority=2)
3. _fallback_to_web_search() (web search 天气)
4. _fallback_to_llm() (LLM 生成回复)

**get_stock**:
1. sina_finance (priority=1)
2. _fallback_to_web_search() (web search 股票)
3. _fallback_to_llm() (LLM 生成回复)

**get_news**:
1. sina_news (priority=1)
2. tavily (priority=2)
3. _fallback_to_web_search() (web search 新闻)
4. _fallback_to_llm() (LLM 生成回复)

## 评测框架中的 Mock 检测

**文件**: `scripts/run_full_eval.py`

**Mock 检测逻辑**:
```python
def validate_result(case: TestCase, response: dict) -> bool:
    # CRITICAL: Reject any mock data
    if tool_provider and "mock" in tool_provider.lower():
        return False
```

**作用**: 任何包含 "mock" 的 provider 都会被标记为失败

## 清理验证总结

| 项目 | 状态 | 备注 |
|------|------|------|
| Provider Config Mock 删除 | ✅ | 3 个 mock provider 配置已删除 |
| Chat Flow Mock 检查删除 | ✅ | mock_search/nearby/trip 已删除 |
| MCP Gateway 注释更新 | ✅ | 所有注释已更新 |
| Weather Client 删除 | ✅ | 已删除弃用的 mock weather 实现 |
| 代码扫描 | ✅ | 无 mock provider 相关代码 |
| 语法检查 | ✅ | 所有文件无诊断错误 |
| 评测框架 Mock 检测 | ✅ | 已有 mock 检测逻辑 |

## 结论

✅ **Mock 数据污染已彻底清理**

- 所有 mock provider 配置已删除
- 所有 mock 相关代码已清理
- 所有 mock 相关文件已删除
- 新的 fallback 链路完全不使用 mock
- 评测框架会拒绝任何包含 mock 的结果

**预期效果**: 评测结果中不会再出现 mock 数据污染

## 下一步

1. 启动服务进行完整评测
2. 验证 200 条评测数据中没有 mock 污染
3. 分析剩余的 23 条失败数据的真实原因
4. 针对性修复其他 provider 的问题
