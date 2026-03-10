# Mock Fallback 完全移除报告

## 执行时间
2026-03-09

## 任务目标
彻底移除所有 mock fallback，实现真实的兜底链路：专用工具失败 → web_search → LLM

## 完成内容

### 1. 新增兜底方法 ✅

在 `agent_service/infra/tool_clients/mcp_gateway.py` 中新增：

#### `_fallback_to_web_search()`
- 当专用工具失败时，使用 web_search 搜索相关信息
- 根据工具类型自动构造搜索query
- 如果 web_search 也失败，继续走 LLM 兜底

#### `_build_search_query()`
- 根据工具类型优化搜索query
- get_weather: "城市 实时天气"
- get_stock: "股票代码 股票 实时行情"
- get_news: "主题 最新新闻"
- find_nearby: "地点 关键词 推荐"
- plan_trip: "目的地 旅游攻略"

#### `_fallback_to_llm()`
- 最终兜底，使用 LLM 生成有帮助的回复
- 明确告知用户无法获取实时数据
- 建议用户使用相关app或网站
- 绝不编造实时数据

### 2. 替换所有 mock 调用 ✅

#### get_weather
```python
# 原来: fallback = weather_client_get_weather(city)
# 现在: return self._fallback_to_web_search(...)
```

#### get_stock
```python
# 原来: fallback = mock_get_stock(target=target)
# 现在: return self._fallback_to_web_search(...)
```

#### web_search
```python
# 原来: fallback = mock_web_search(query=query)
# 现在: return self._fallback_to_llm(...)
```

#### get_news
```python
# 原来: fallback = mock_get_news(topic=topic)
# 现在: return self._fallback_to_web_search(...)
```

#### find_nearby
```python
# 原来: fallback = mock_find_nearby(keyword=keyword, city=city)
# 现在: return self._fallback_to_web_search(...)
```

#### plan_trip
```python
# 原来: return mock_plan_trip(destination=destination)
# 现在: return self._fallback_to_llm(...)
```

### 3. 删除 mock 相关文件 ✅

- ✅ `agent_service/infra/tool_clients/mock_clients.py`
- ✅ `agent_service/infra/tool_clients/providers/mock_provider.py`
- ✅ 从 `providers/__init__.py` 移除 MockProvider 导入

### 4. 移除旧方法 ✅

- ✅ 删除 `_network_fallback()` 方法（已被新方法替代）
- ✅ 移除 `weather_client_get_weather` 导入

## 新兜底链路

### 场景1: 天气查询
```
用户: 北京今天天气怎么样
系统: Amap MCP → QWeather → web_search("北京 实时天气") → LLM
```

### 场景2: 股票查询
```
用户: 比亚迪今天股价多少
系统: Sina Finance → web_search("比亚迪 股票 实时行情") → LLM
```

### 场景3: 新闻查询
```
用户: 科技新闻
系统: Baidu News → Sina News → web_search("科技 最新新闻") → LLM
```

### 场景4: 地点查询
```
用户: 北京附近的咖啡厅
系统: Amap MCP → Baidu Maps MCP → web_search("北京 咖啡厅 推荐") → LLM
```

### 场景5: 行程规划
```
用户: 上海2日游
系统: Plan Trip Engine → LLM("上海 2日游 旅游攻略")
```

### 场景6: 网页搜索
```
用户: 搜索人工智能
系统: Bing → Tavily → Baidu → LLM
```

## 代码质量检查

### 语法检查 ✅
```bash
python -m py_compile agent_service/infra/tool_clients/mcp_gateway.py
python -m py_compile agent_service/infra/tool_clients/providers/__init__.py
```
结果：无错误

### 诊断检查 ✅
```bash
getDiagnostics(["agent_service/infra/tool_clients/mcp_gateway.py"])
```
结果：No diagnostics found

## 下一步

### 1. 重启服务
```bash
# 停止现有服务
pkill -f "uvicorn agent_service.app.api.server:app"

# 重启服务
source .venv/bin/activate
uvicorn agent_service.app.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 运行评测
```bash
python scripts/run_full_eval.py \
  --dataset archive/csv_data/testset_200条_0309.csv \
  --output eval/reports/eval_200_no_mock_$(date +%Y%m%d_%H%M%S)
```

### 3. 验证结果
- 检查是否还有 mock 数据（tool_provider 字段）
- 对比准确率变化
- 分析 bad case

## 预期效果

### 准确率
- 之前（含mock污染）: 61.5% (123/200)
- 真实准确率（移除mock后）: 46.5% (93/200)
- 预期（新兜底链路）: 55-65% (110-130/200)

### 提升来源
1. web_search 兜底可以回答大部分实时信息查询
2. LLM 兜底提供有帮助的通用建议
3. 无假数据，所有结果都是真实的

### 用户体验
- 即使专用工具失败，仍能提供有价值的信息
- 明确告知用户数据来源和限制
- 建议用户使用相关app获取实时数据

## 技术亮点

1. **三层兜底**: 专用工具 → web_search → LLM
2. **智能降级**: 根据工具类型自动构造搜索query
3. **透明度**: 在返回结果中标注兜底链路
4. **无假数据**: 彻底移除mock，保证数据真实性
5. **用户友好**: LLM 兜底提供有帮助的建议而非错误信息

## 风险与限制

### 风险
1. LLM 响应时间可能较长（5-10秒）
2. web_search 可能返回不相关结果
3. 某些查询可能无法通过 web_search 获取准确信息

### 缓解措施
1. 设置合理的超时时间
2. 优化搜索query构造逻辑
3. LLM prompt 明确要求不编造数据

### 限制
1. 无法获取实时数据时，只能提供通用建议
2. 依赖 LM Studio 服务可用性
3. 依赖 web_search 服务质量

## 总结

✅ 已完全移除所有 mock fallback
✅ 实现了真实的三层兜底链路
✅ 代码质量检查通过
✅ 准备好进行评测验证

下一步：重启服务并运行200条评测，验证新兜底链路的效果。
