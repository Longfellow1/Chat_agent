# 规则优先的产品优化策略

## 核心理念

**设计理念**：规则优先处理高频场景，LLM 兜底长尾需求（动态决策，非固定比例）

### 设计哲学

```
高频简单场景 → 规则处理 → 快速、准确、低成本
复杂推荐场景 → 规则 + LLM → 平衡性能和体验
长尾特殊场景 → 纯 LLM → 保证覆盖率
```

### 三大收益

1. **性能**：规则处理延迟 < 100ms，LLM 需要 500-1500ms（单节点不超1500ms）
2. **成本**：规则零成本，LLM 每次调用消耗 token
3. **稳定性**：规则确定性输出，LLM 存在幻觉风险

### 规则处理的质量要求

1. **自然流畅**：使用多样化模板，避免机械感话术
2. **结果优化**：对API返回的候选结果进行排序rerank

---

## 通用优化框架

### 四阶段处理流程

```
用户 Query
    ↓
[1] Query 结构化（Intent Parsing）
    ↓
[2] 参数补全与验证（Completion & Validation）
    ↓
[3] 工具调用与结果获取（Tool Execution）
    ↓
[4] 结果后处理（Post-Processing: Rerank + Template）
    ↓
最终响应
```

### 阶段 1：Query 结构化

**目标**：从自然语言提取结构化字段

**策略**：
- 规则优先：正则表达式 + 词典匹配（覆盖高频 pattern）
- LLM 兜底：规则提取不完整时，LLM 补全缺失字段

**通用模式**：
```python
def parse_intent(query: str, tool_name: str) -> Intent:
    """通用意图解析框架"""
    # 1. 规则快速路径
    intent = extract_by_rules(query, tool_name)
    
    # 2. 完整性检查
    if intent.is_complete():
        return intent
    
    # 3. LLM 补全缺失字段
    intent = complete_by_llm(query, intent, tool_name)
    
    return intent
```

---

### 阶段 2：参数补全与验证

**目标**：确保工具调用参数完整且合法

**策略**：
- 必填字段验证：缺失时返回错误，要求用户补充
- 格式标准化：统一日期、数字、枚举格式
- 注意：使用高德MCP接口，不直接调用高德Web API

---

### 阶段 3：工具调用与结果获取

**目标**：高效调用外部 API 并处理异常

**策略**：
- 多跳检索：复杂查询拆分为多次 API 调用
- 并行调用：独立查询并行执行
- 错误透传：网络/API错误直接返回给用户，不隐藏

**通用模式**：
```python
def execute_tool(tool_name: str, params: dict) -> ToolResult:
    """通用工具执行框架"""
    try:
        # 1. 判断是否需要多跳
        if requires_multi_hop(tool_name, params):
            return execute_multi_hop(tool_name, params)
        
        # 2. 单跳调用
        result = call_api(tool_name, params)
        
        return ToolResult(ok=True, data=result)
    
    except NetworkError as e:
        # 3. 错误透传给用户
        return ToolResult(
            ok=False,
            error=f"网络错误：{e.message}",
            error_type="network_error"
        )
    
    except APIError as e:
        # 4. API错误透传
        return ToolResult(
            ok=False,
            error=f"服务暂时不可用：{e.message}",
            error_type="api_error"
        )
```

---

### 阶段 4：结果后处理（Rerank + Template）

**目标**：优化结果质量和用户体验

**策略**：
- 规则过滤：移除噪声数据
- 规则排序：按用户意图重排序（Rerank）
- 规则聚合：多源结果合并去重
- 模板输出：使用多样化模板，自然流畅
- LLM 润色：复杂场景用 LLM 生成自然语言

**通用模式**：
```python
def post_process(
    results: list[dict],
    intent: Intent,
    tool_name: str
) -> ProcessedResult:
    """通用结果后处理框架"""
    # 1. 规则过滤（责任链模式）
    filtered = apply_filters(results, intent, tool_name)
    
    # 2. 规则排序（策略模式 - Rerank）
    sorted_results = apply_sorting(filtered, intent, tool_name)
    
    # 3. 数量控制
    final = apply_limit(sorted_results, intent)
    
    # 4. 判断是否需要 LLM 润色
    if should_use_llm_polish(intent, tool_name, final):
        text = llm_polish(final, intent, tool_name)
    else:
        # 5. 模板填槽（多样化模板，避免机械感）
        text = format_by_template(final, intent, tool_name)
        
        # 6. 模板失败降级：直接返回API结果
        if not text:
            text = format_api_raw(final)
    
    return ProcessedResult(data=final, text=text)
```

**责任链过滤器示例**：
```python
class ResultProcessor(ABC):
    """结果处理器基类"""
    priority: int = 100
    
    @abstractmethod
    def process(self, results: list[dict], intent: Intent) -> list[dict]:
        pass

# 具体过滤器
class BrandFilter(ResultProcessor):
    """品牌过滤器"""
    priority = 10
    
    def process(self, results: list[dict], intent: Intent) -> list[dict]:
        if not intent.brand:
            return results
        return [r for r in results if intent.brand in r["name"]]

class DistanceSorter(ResultProcessor):
    """距离排序器（Rerank）"""
    priority = 50
    
    def process(self, results: list[dict], intent: Intent) -> list[dict]:
        if intent.sort_by != "distance":
            return results
        return sorted(results, key=lambda r: r.get("distance", 999999))
```

**多样化模板示例**：
```python
def format_by_template(results: list[dict], intent: Intent, tool_name: str) -> str:
    """使用随机模板填槽，避免机械感"""
    templates = get_templates(tool_name, intent)
    
    # 随机选择一个模板
    template = random.choice(templates)
    
    try:
        # 尝试填槽
        return template.format(**extract_fields(results, intent))
    except KeyError:
        # 填槽失败，返回空（触发降级）
        return ""

# 天气场景模板示例
WEATHER_TEMPLATES = [
    "{city}今天{weather}，气温{temp}",
    "{city}当前{weather}，温度{temp}，{suggestion}",
    "今天{city}{weather}，{temp}，{suggestion}",
    "{city}的天气是{weather}，{temp}左右"
]
```

---

## LLM 使用决策

### 何时跳过 LLM（规则直出）

**场景 1：简单查询 + 结构化结果**
```python
# 示例：天气查询
query = "北京今天天气"
intent = WeatherIntent(city="北京", date="今天")
result = {"city": "北京", "temp": "15°C", "weather": "晴"}

# 随机模板填槽
templates = WEATHER_TEMPLATES
text = random.choice(templates).format(**result)
# 输出："北京今天晴，气温15°C" 或 "今天北京晴，15°C左右"
```

**场景 2：单一结果 + 明确意图**
```python
# 示例：股票查询
query = "茅台股价"
intent = StockIntent(target="600519.SS")
result = {"name": "贵州茅台", "price": "1680.50", "change": "+2.3%"}

# 随机模板填槽
templates = STOCK_TEMPLATES
text = random.choice(templates).format(**result)
# 输出："贵州茅台最新价1680.50，涨幅+2.3%"
```

### 何时使用 LLM（润色增强）

**场景 1：推荐类查询（主观判断）**
```python
# 示例：附近餐厅推荐
query = "鸟巢附近推荐好吃的餐厅"
results = [
    {"name": "左庭右院", "rating": 4.8, "price": 150},
    {"name": "海底捞", "rating": 4.6, "price": 120},
]

# 必须使用 LLM（涉及主观推荐）
# 输出："在国家体育场附近，推荐您去左庭右院，评分4.8分..."
```

**场景 2：对比类查询**
```python
# 示例：多股票对比
query = "茅台和五粮液哪个更值得买"
results = [...]

# 必须使用 LLM（涉及对比分析）
```

**场景 3：解释类查询**
```python
# 示例：为什么涨了
query = "茅台为什么涨了"

# 必须使用 LLM（需要解释）
```

**判断条件**：
```python
def should_use_llm(intent: Intent, results: list[dict], tool_name: str) -> bool:
    """判断是否使用 LLM 后处理"""
    # 1. 涉及"推荐"等主观需求 → 必须使用 LLM
    if intent.requires_recommendation():
        return True
    
    # 2. 对比类查询 → 使用 LLM
    if intent.query_type == "comparison":
        return True
    
    # 3. 解释类查询 → 使用 LLM
    if intent.requires_explanation():
        return True
    
    # 4. 长文本需要摘要 → 使用 LLM
    total_length = sum(len(str(r)) for r in results)
    if total_length > 1000:
        return True
    
    # 5. 新闻/搜索类工具 → 使用 LLM
    if tool_name in {"get_news", "web_search"}:
        return True
    
    return False
```

---

## 工具级配置策略

### 配置字典

```python
TOOL_OPTIMIZATION_CONFIG = {
    "find_nearby": {
        "use_intent_parsing": True,
        "use_multi_hop": True,
        "use_result_rerank": True,
        "use_template_response": True,  # 优先使用模板
        "llm_timeout_sec": 10,
        "max_llm_time_ms": 1500,  # 单节点不超1500ms
    },
    "get_weather": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": False,
        "use_template_response": True,  # 优先使用模板
        "llm_timeout_sec": 6,
        "max_llm_time_ms": 1500,
    },
    "get_stock": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": True,  # 需要按涨跌幅排序
        "use_template_response": True,  # 优先使用模板
        "llm_timeout_sec": 6,
        "max_llm_time_ms": 1500,
    },
    "get_news": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": True,
        "use_template_response": False,  # 必须LLM摘要
        "llm_timeout_sec": 15,
        "max_llm_time_ms": 1500,
    },
    "web_search": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": True,
        "use_template_response": False,  # 必须LLM处理
        "llm_timeout_sec": 10,
        "max_llm_time_ms": 1500,
    },
}
```

**注意**：不再预设固定的"跳过LLM比例"，而是通过动态决策函数判断。

### 动态决策函数

```python
def should_skip_post_llm(
    tool_name: str,
    intent: Intent,
    results: list[dict]
) -> bool:
    """通用 LLM 跳过决策 - 基于多维度判断"""
    config = TOOL_OPTIMIZATION_CONFIG.get(tool_name, {})
    
    # 1. 工具级强制配置
    if not config.get("use_template_response", True):
        # 新闻/搜索类必须用LLM
        return False
    
    # 2. 意图类型判断
    if intent.requires_recommendation():
        # 推荐类必须用LLM（主观判断）
        return False
    
    if intent.query_type == "comparison":
        # 对比类必须用LLM
        return False
    
    if intent.requires_explanation():
        # 解释类必须用LLM
        return False
    
    # 3. 结果质量判断
    if not results or len(results) == 0:
        # 无结果，需要LLM解释
        return False
    
    # 4. 模板可用性判断
    if can_fill_template(results, intent, tool_name):
        # 模板能填槽，跳过LLM
        return True
    
    # 5. 默认：使用LLM
    return False

def can_fill_template(results: list[dict], intent: Intent, tool_name: str) -> bool:
    """判断模板是否能成功填槽"""
    templates = get_templates(tool_name, intent)
    if not templates:
        return False
    
    # 检查必填字段是否存在
    required_fields = get_required_fields(tool_name)
    for field in required_fields:
        if not any(field in r for r in results):
            return False
    
    return True
```

---

## 实施计划

### Phase 1：Result Rerank 模块（当前任务）

**目标**：实现结果后处理的 Rerank 功能

**任务**：
1. 创建 `agent_service/domain/location/result_processor.py`
2. 实现 `ResultProcessor` 基类
3. 实现具体策略：
   - `DistanceSorter`：按距离排序
   - `RatingSorter`：按评分排序
   - `BrandFilter`：品牌过滤
   - `TopNSelector`：数量控制
4. 实现 `ResultProcessorChain` 责任链管理器
5. 在 `mcp_gateway_v2.py` 中集成调用
6. 编写测试用例

### Phase 2：Template Response 模块

**目标**：实现多样化模板输出

**任务**：
1. 创建模板管理模块
2. 为每个工具定义多样化模板
3. 实现随机模板选择和填槽
4. 实现降级策略

### Phase 3：LLM Decision 模块

**目标**：实现动态 LLM 决策

**任务**：
1. 实现意图类型识别
2. 实现 `should_skip_post_llm` 决策函数
3. 集成到 `chat_flow.py`

---

**文档版本**：v2.0  
**创建日期**：2026-03-03  
**适用范围**：所有工具优化（Location, Weather, Stock, News, Search）  
**维护者**：Kiro AI Assistant
