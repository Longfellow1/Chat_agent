# Web Search 完整指南

> 联网搜索工具的完整文档，包含架构设计、实现细节和优化策略

---

## 📚 目录

1. [产品定位](#产品定位)
2. [架构设计](#架构设计)
3. [核心模块](#核心模块)
4. [性能优化](#性能优化)
5. [测试结果](#测试结果)
6. [配置说明](#配置说明)

---

## 产品定位

### 核心定位

联网搜索是**万能兜底工具**，承担以下职责：

1. **信息查询兜底**：所有不属于垂直领域但需要联网的问题
2. **实时数据获取**：可变信息、需核验真实性的内容
3. **知识验证补充**：生活常识验证、百科知识查询
4. **动态内容追踪**：明星动态、赛事结果、产品价格

### 与其他工具的边界

| 工具类型 | 适用场景 | 联网搜索的边界 |
|---------|---------|--------------|
| 天气查询 | 明确的气象查询 | 不处理 |
| 股票查询 | 金融二级市场数据 | 不处理 |
| 行程规划 | 旅行决策 | 不处理 |
| 新闻资讯 | "正在发生"的时事 | 不处理 |
| 周边搜索 | 具体地点附近的POI | 不处理 |
| 联网搜索 | 上述之外的所有需要联网的查询 | **万能兜底** |

---

## 架构设计

### 整体架构

```
User Query
    ↓
┌─────────────────────────────────────┐
│  Intent Router (domain/intents)     │
│  - 规则优先：route_query()           │
│  - LLM兜底：_route_with_llm()        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Query Optimization                 │
│  - 停用词去除                        │
│  - 时间标准化                        │
│  - 实体类型识别                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Search Execution (Tavily API)      │
│  - 超时：3秒                         │
│  - 降级策略：mock_web_search()       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Result Processing                  │
│  - 相关性过滤                        │
│  - 去重逻辑                          │
│  - 可信度评分                        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  LLM Post-Processing                │
│  - 超时：5秒                         │
│  - 字数限制：150字                   │
└─────────────────────────────────────┘
```

---

## 核心模块

### 1. Intent Router

**位置**：`agent_service/domain/intents/web_search_router.py`

**关键词配置**：

```python
strong_keywords=(
    # 搜索行为
    "官网", "官方网站", "网址", "链接", "搜索", "搜一下", "查资料", "百度一下",
    # 信息查询
    "查询", "查一下", "找一下", "了解一下", "知道", "告诉我",
    # 验证类
    "是真的吗", "真的假的", "确认一下", "核实一下",
    # 最新信息
    "最新", "近期", "最近", "现在", "目前", "当前",
    # 动态信息
    "价格", "多少钱", "售价", "报价",
)
```

**排除模式**：

```python
exclude_patterns=(
    r"(天气|气温|下雨|空气)",  # 天气类
    r"(股票|股价|涨跌)",      # 股票类
    r"(附近|周边|导航)",      # 地点类
)
```

### 2. Query Optimization

**位置**：`agent_service/domain/tools/query_preprocessor.py`

**功能**：
- 停用词去除
- 时间标准化（动态年份）
- 实体类型识别（person/concept/product/event）
- 关键词提取

**示例**：

```python
query = "帮我查一下最新的iPhone价格"
↓
optimized_query = "iPhone价格 2026"
entity_type = "product"
keywords = ["iPhone", "价格"]
```

### 3. Result Processing

**位置**：`agent_service/infra/tool_clients/search_result_processor.py`

**功能**：
1. **相关性过滤**：计算查询与结果的相关性得分
2. **去重逻辑**：基于标题相似度去重（阈值 0.8）
3. **可信度评分**：基于来源域名评分（0-10分）
4. **综合排序**：相关性 70% + 可信度 30%

**可信度规则**：

```python
DOMAIN_SCORE_MAP = {
    ".gov.cn": 10,  # 政府网站
    ".edu.cn": 9,   # 教育机构
    ".org.cn": 8,   # 组织机构
}

TRUSTED_DOMAINS = {
    "xinhuanet.com": 10,
    "people.com.cn": 10,
    "zhihu.com": 7,
    "baike.baidu.com": 6,
}
```

### 4. LLM Post-Processing

**位置**：`agent_service/app/orchestrator/chat_flow.py`

**专用 Prompt**：

```python
TOOL_POST_PROMPT_SEARCH = (
    "你是网络搜索结果总结助手。"
    "请基于搜索结果生成简洁、准确、自然的中文回复。"
    "严格限制：总字数不超过150字。"
    "必须基于搜索结果回答，不能编造信息。"
    "如果结果不相关，明确告知用户'未找到相关信息'。"
    "优先保留：关键信息、来源标记（[官方]、[可信]）。"
)
```

---

## 性能优化

### 超时配置

| 配置项 | 原值 | 优化后 | 说明 |
|--------|------|--------|------|
| Tavily 超时 | 8s | 3s | 避免过长等待 |
| LLM 总结超时 | 10s | 5s | 平衡性能和稳定性 |

### 输入精简

- 只保留前3条结果
- 限制 title 100字、snippet 80字
- 减少 token 消耗约 50%

### 降级策略

```python
def _web_search_with_fallback(self, query: str) -> ToolResult:
    try:
        return self._web_search(query, timeout=3.0)
    except TimeoutError:
        return mock_web_search(query=query, reason="timeout")
```

---

## 测试结果

### 单元测试汇总

```
tests/unit/test_query_preprocessor.py:        12/12 ✅
tests/unit/test_web_search_router.py:         21/21 ✅
tests/unit/test_search_result_processor.py:   18/18 ✅
tests/unit/test_planner_web_search.py:        14/14 ✅
---------------------------------------------------
总计:                                          65/65 ✅
```

### 功能完整度

| 模块 | 完整度 |
|------|--------|
| Intent Router | 100% |
| Query Optimization | 100% |
| Search Execution | 100% |
| Result Processing | 100% |
| Post-Processing | 100% |
| **核心功能** | **100%** |

---

## 配置说明

### 环境变量

```bash
# Tavily API
TAVILY_API_KEY=your_api_key
TAVILY_TIMEOUT_SEC=3.0

# 超时配置
TOOL_POST_LLM_TIMEOUT_SEARCH_SEC=5.0
ENABLE_TIMEOUT_FALLBACK=true

# 结果配置
TOOL_SEARCH_MAX_RESULTS=3
TOOL_SEARCH_SNIPPET_CHARS=80
```

### 文件清单

**核心模块**：
- `agent_service/domain/intents/web_search_router.py` - Intent Router
- `agent_service/domain/tools/query_preprocessor.py` - Query Preprocessor
- `agent_service/infra/tool_clients/search_result_processor.py` - Result Processing
- `agent_service/infra/tool_clients/mcp_gateway.py` - Search Execution
- `agent_service/app/orchestrator/chat_flow.py` - Post-Processing

**测试文件**：
- `tests/unit/test_web_search_router.py` - 21个测试
- `tests/unit/test_query_preprocessor.py` - 12个测试
- `tests/unit/test_search_result_processor.py` - 18个测试
- `tests/unit/test_planner_web_search.py` - 14个测试

---

## 关键改进总结

### 1. 结果质量提升
- ✅ 相关性过滤：过滤不相关结果
- ✅ 去重：避免重复结果
- ✅ 可信度评分：优先展示可信来源
- ✅ 综合排序：相关性 + 可信度

### 2. 查询优化
- ✅ 停用词去除：提升搜索精准度
- ✅ 时间标准化：动态年份补充
- ✅ 实体识别：理解查询意图
- ✅ 关键词提取：提升相关性判断

### 3. 性能优化
- ✅ 超时配置优化：避免过长等待
- ✅ 输入精简：减少 token 消耗 50%
- ✅ 专用 Prompt：提升生成质量
- ✅ 字数限制：150字以内

### 4. 用户体验
- ✅ 可信度标记：[官方]、[可信]
- ✅ 结果排序：最相关的在前
- ✅ 明确提示：无相关结果时告知
- ✅ 来源追溯：保留 URL

---

## 使用示例

### 基础使用

```python
from domain.intents.web_search_router import route_web_search
from domain.tools.query_preprocessor import preprocess_query
from infra.tool_clients.mcp_gateway import MCPToolGateway

# 1. 路由判断
if route_web_search(query):
    # 2. 查询优化
    optimized = preprocess_query(query)
    
    # 3. 执行搜索
    gateway = MCPToolGateway()
    result = gateway._web_search(optimized["query"])
    
    # 4. LLM 总结
    final_text = llm_summarize(result.text)
```

---

## 常见问题

### Q: 如何添加新的关键词？

编辑 `agent_service/domain/intents/web_search_router.py`，添加到 `strong_keywords` 或 `weak_keywords`。

### Q: 如何调整超时时间？

修改环境变量：
- `TAVILY_TIMEOUT_SEC`：Tavily API 超时
- `TOOL_POST_LLM_TIMEOUT_SEARCH_SEC`：LLM 总结超时

### Q: 如何添加新的可信来源？

编辑 `agent_service/infra/tool_clients/search_result_processor.py`，添加到 `TRUSTED_DOMAINS`。

---

**文档版本**：v2.0（合并版）  
**创建日期**：2026-03-06  
**合并自**：web_search_tool_architecture.md, web_search_tool_review.md, web_search_phase2_completion_summary.md  
**状态**：✅ 生产就绪
