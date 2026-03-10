# 规则优先的产品优化策略

## 核心理念

**80/20 原则**：规则解决 80% 高频场景，LLM 兜底 20% 长尾需求

### 设计哲学

```
高频场景（80%）→ 规则处理 → 快速、准确、低成本
复杂场景（15%）→ 规则 + LLM → 平衡性能和体验
长尾场景（5%） → 纯 LLM → 保证覆盖率
```

### 三大收益

1. **性能**：规则处理延迟 < 100ms，LLM 需要 500-2000ms
2. **成本**：规则零成本，LLM 每次调用消耗 token
3. **稳定性**：规则确定性输出，LLM 存在幻觉风险

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
[4] 结果后处理（Post-Processing）
    ↓
最终响应
```

### 阶段 1：Query 结构化

**目标**：从自然语言提取结构化字段

**策略**：
- 规则优先：正则表达式 + 词典匹配（覆盖 80% 高频 pattern）
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

**适用场景**：
- Location：城市、地点、品牌、类别、排序
- Stock：股票代码、公司名、指数
- Weather：城市、日期、指标类型
- Search：关键词、时间范围、来源

---

### 阶段 2：参数补全与验证

**目标**：确保工具调用参数完整且合法

**策略**：
- 别名映射：通俗名 → 标准名（鸟巢 → 国家体育场）
- 默认值填充：缺失非必填字段时使用合理默认值
- 格式标准化：统一日期、数字、枚举格式

**通用模式**：
```python
def complete_and_validate(intent: Intent, tool_name: str) -> dict[str, Any]:
    """通用参数补全与验证"""
    # 1. 别名解析
    params = resolve_aliases(intent, tool_name)
    
    # 2. 默认值填充
    params = fill_defaults(params, tool_name)
    
    # 3. 格式标准化
    params = normalize_format(params, tool_name)
    
    # 4. 必填字段验证
    missing = validate_required(params, tool_name)
    if missing:
        raise MissingFieldsError(missing)
    
    return params
```

**词典管理**：
```python
# 通用别名词典结构
ALIAS_DICTIONARIES = {
    "location": {
        "landmarks": {"鸟巢": "国家体育场", ...},
        "brands": {"711": "7-11", ...},
        "categories": {"便利店": "购物服务;便利店", ...}
    },
    "stock": {
        "companies": {"茅台": "600519.SS", "京东": "JD", ...},
        "indices": {"上证": "000001.SS", "深证": "399001.SZ", ...}
    },
    "weather": {
        "cities": {"帝都": "北京", "魔都": "上海", ...},
        "indicators": {"穿衣": "dressing_index", ...}
    }
}
```

---

### 阶段 3：工具调用与结果获取

**目标**：高效调用外部 API 并处理异常

**策略**：
- 多跳检索：复杂查询拆分为多次 API 调用
- 并行调用：独立查询并行执行
- 降级策略：API 失败时使用 mock 或缓存

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
    
    except NetworkError:
        # 3. 降级策略
        return fallback_strategy(tool_name, params)
```

**多跳检索示例（Location）**：
```python
def execute_multi_hop_location(params: dict) -> ToolResult:
    """两跳检索：先定位锚点，再搜周边"""
    # 跳 1：定位锚点 POI
    anchor = search_anchor(params["anchor_poi"], params["city"])
    
    # 跳 2：周边搜索目标
    results = search_around(
        location=anchor.location,
        keyword=params["keyword"],
        radius=1000
    )
    
    return ToolResult(ok=True, data=results, anchor=anchor)
```

---

### 阶段 4：结果后处理

**目标**：优化结果质量和用户体验

**策略**：
- 规则过滤：移除噪声数据
- 规则排序：按用户意图重排序
- 规则聚合：多源结果合并去重
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
    
    # 2. 规则排序（策略模式）
    sorted_results = apply_sorting(filtered, intent, tool_name)
    
    # 3. 数量控制
    final = apply_limit(sorted_results, intent)
    
    # 4. 判断是否需要 LLM 润色
    if should_use_llm_polish(intent, tool_name, final):
        text = llm_polish(final, intent, tool_name)
    else:
        text = format_by_template(final, intent, tool_name)
    
    return ProcessedResult(data=final, text=text)
```

**责任链过滤器**：
```python
class ResultProcessor(ABC):
    """结果处理器基类"""
    priority: int = 100
    
    @abstractmethod
    def process(self, results: list[dict], intent: Intent) -> list[dict]:
        pass

# 具体过滤器示例
class BrandFilter(ResultProcessor):
    """品牌过滤器"""
    priority = 10
    
    def process(self, results: list[dict], intent: Intent) -> list[dict]:
        if not intent.brand:
            return results
        return [r for r in results if intent.brand in r["name"]]

class DistanceSorter(ResultProcessor):
    """距离排序器"""
    priority = 50
    
    def process(self, results: list[dict], intent: Intent) -> list[dict]:
        if intent.sort_by != "distance":
            return results
        return sorted(results, key=lambda r: r.get("distance", 999999))
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

# 规则模板直出
text = f"{result['city']}今天{result['weather']}，气温{result['temp']}"
# 输出："北京今天晴，气温15°C"
```

**场景 2：单一结果 + 明确意图**
```python
# 示例：股票查询
query = "茅台股价"
intent = StockIntent(target="600519.SS")
result = {"name": "贵州茅台", "price": "1680.50", "change": "+2.3%"}

# 规则模板直出
text = f"{result['name']}最新价{result['price']}，涨幅{result['change']}"
# 输出："贵州茅台最新价1680.50，涨幅+2.3%"
```

**判断条件**：
```python
def should_skip_llm(intent: Intent, results: list[dict], tool_name: str) -> bool:
    """判断是否跳过 LLM 后处理"""
    # 1. 结果为空或错误 → 需要 LLM 解释
    if not results or results[0].get("error"):
        return False
    
    # 2. 单一结果 + 简单意图 → 跳过 LLM
    if len(results) == 1 and intent.is_simple():
        return True
    
    # 3. 结果已足够简洁（< 200 字符）→ 跳过 LLM
    text = format_by_template(results, intent, tool_name)
    if len(text) < 200:
        return True
    
    # 4. 高频工具 + 标准格式 → 跳过 LLM
    if tool_name in {"get_weather", "get_stock"} and is_standard_format(results):
        return True
    
    return False
```

### 何时使用 LLM（润色增强）

**场景 1：多结果推荐**
```python
# 示例：附近餐厅推荐
query = "鸟巢附近好吃的餐厅"
results = [
    {"name": "左庭右院", "rating": 4.8, "price": 150},
    {"name": "海底捞", "rating": 4.6, "price": 120},
    {"name": "外婆家", "rating": 4.5, "price": 80}
]

# 需要 LLM 生成推荐语
# 输出："在国家体育场附近，推荐您去左庭右院，评分4.8分，人均150元，
#       口碑很好。如果想吃火锅，海底捞也是不错的选择。"
```

**场景 2：复杂对比**
```python
# 示例：多股票对比
query = "茅台和五粮液哪个更值得买"
results = [
    {"name": "贵州茅台", "price": 1680, "pe": 35, "roe": 28},
    {"name": "五粮液", "price": 180, "pe": 28, "roe": 25}
]

# 需要 LLM 生成对比分析
# 输出："贵州茅台和五粮液都是白酒龙头，茅台估值较高但盈利能力更强，
#       五粮液性价比更好。建议根据您的风险偏好选择。"
```

**场景 3：长文本摘要**
```python
# 示例：新闻搜索
query = "今天科技新闻"
results = [
    {"title": "...", "content": "500字新闻正文..."},
    {"title": "...", "content": "600字新闻正文..."}
]

# 需要 LLM 提取关键信息并摘要
```

**判断条件**：
```python
def should_use_llm(intent: Intent, results: list[dict], tool_name: str) -> bool:
    """判断是否使用 LLM 后处理"""
    # 1. 多结果需要推荐 → 使用 LLM
    if len(results) > 3 and intent.requires_recommendation():
        return True
    
    # 2. 对比类查询 → 使用 LLM
    if intent.query_type == "comparison":
        return True
    
    # 3. 长文本需要摘要 → 使用 LLM
    total_length = sum(len(str(r)) for r in results)
    if total_length > 1000:
        return True
    
    # 4. 新闻/搜索类工具 → 使用 LLM
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
        "skip_llm_threshold": 0.8,  # 80% 场景跳过 LLM
        "llm_timeout_sec": 10,
    },
    "get_weather": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": False,
        "skip_llm_threshold": 0.9,  # 90% 场景跳过 LLM
        "llm_timeout_sec": 6,
    },
    "get_stock": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": True,  # 需要按涨跌幅排序
        "skip_llm_threshold": 0.85,
        "llm_timeout_sec": 6,
    },
    "get_news": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": True,
        "skip_llm_threshold": 0.2,  # 80% 场景需要 LLM 摘要
        "llm_timeout_sec": 16,
    },
    "web_search": {
        "use_intent_parsing": True,
        "use_multi_hop": False,
        "use_result_rerank": True,
        "skip_llm_threshold": 0.3,
        "llm_timeout_sec": 10,
    },
}
```

### 动态决策函数

```python
def should_skip_post_llm(
    tool_name: str,
    intent: Intent,
    results: list[dict]
) -> bool:
    """通用 LLM 跳过决策"""
    config = TOOL_OPTIMIZATION_CONFIG.get(tool_name, {})
    threshold = config.get("skip_llm_threshold", 0.5)
    
    # 计算规则处理置信度
    confidence = calculate_rule_confidence(intent, results, tool_name)
    
    # 置信度高于阈值 → 跳过 LLM
    return confidence >= threshold

def calculate_rule_confidence(
    intent: Intent,
    results: list[dict],
    tool_name: str
) -> float:
    """计算规则处理置信度"""
    score = 0.0
    
    # 1. 意图完整性（0-0.3）
    if intent.is_complete():
        score += 0.3
    
    # 2. 结果质量（0-0.4）
    if results and len(results) <= 3:
        score += 0.2
    if results and all(r.get("confidence", 0) > 0.8 for r in results):
        score += 0.2
    
    # 3. 查询复杂度（0-0.3）
    if intent.query_type == "simple":
        score += 0.3
    elif intent.query_type == "moderate":
        score += 0.15
    
    return min(score, 1.0)
```

---

## 各工具优化路线图

### Location（已实现）

- [x] Query 结构化：城市、地点、品牌、类别、排序
- [x] 两跳检索：先定位锚点，再搜周边
- [ ] 结果 Rerank：距离、评分、价格排序
- [ ] LLM 决策：简单查询跳过，推荐场景使用

### Weather（待优化）

**高频场景**：
- "北京今天天气" → 规则直出
- "明天穿什么" → 规则 + 穿衣指数
- "这周会下雨吗" → 规则 + 7 天预报

**优化方向**：
```python
class WeatherIntent:
    city: str
    date: str  # 今天/明天/这周
    indicator: str  # 穿衣/紫外线/空气质量
    query_type: str  # simple/forecast/index
```

**Rerank 需求**：
- 按日期排序（今天 → 明天 → 后天）
- 过滤无关指数
- 格式化温度范围

### Stock（待优化）

**高频场景**：
- "茅台股价" → 规则直出
- "上证指数" → 规则直出
- "科技股涨幅榜" → 规则 Rerank + LLM 推荐

**优化方向**：
```python
class StockIntent:
    target: str  # 股票代码/公司名/指数
    metric: str  # price/change/volume
    sort_by: str  # change/volume/market_cap
    query_type: str  # single/ranking/comparison
```

**Rerank 需求**：
- 按涨跌幅排序
- 按成交量排序
- 过滤停牌股票

### News（待优化）

**高频场景**：
- "今天新闻" → LLM 摘要（必须）
- "科技新闻" → LLM 摘要（必须）
- "某公司最新消息" → LLM 摘要（必须）

**优化方向**：
```python
class NewsIntent:
    topic: str
    time_range: str  # today/week/month
    source: str  # all/tech/finance
    limit: int = 5
```

**Rerank 需求**：
- 按时间排序（最新优先）
- 按相关性排序
- 去重相似新闻

### Web Search（待优化）

**高频场景**：
- "某公司官网" → 规则直出第一条
- "某技术教程" → LLM 摘要
- "某产品对比" → LLM 对比分析

**优化方向**：
```python
class SearchIntent:
    query: str
    intent_type: str  # official_site/tutorial/comparison/general
    limit: int = 5
```

**Rerank 需求**：
- 官网优先
- 按相关性排序
- 过滤低质量结果

---

## 实施原则

### 1. 渐进式优化

```
Phase 1: Location（已完成）
    ↓
Phase 2: Weather + Stock（高频工具）
    ↓
Phase 3: News + Search（长文本工具）
    ↓
Phase 4: 其他工具
```

### 2. 数据驱动

- 收集真实用户 query 分布
- 统计各场景占比
- 优先优化 Top 20% 高频场景

### 3. 可观测性

```python
# 记录每次决策
@dataclass
class OptimizationMetrics:
    tool_name: str
    intent_confidence: float
    rule_applied: bool
    llm_skipped: bool
    latency_ms: int
    user_satisfaction: float  # 用户反馈
```

### 4. A/B 测试

- 规则版 vs LLM 版
- 对比延迟、成本、满意度
- 动态调整 `skip_llm_threshold`

---

## 成功指标

| 指标 | 当前 | 目标 | 备注 |
|------|------|------|------|
| 规则覆盖率 | 40% | 80% | 高频场景规则处理占比 |
| LLM 调用率 | 60% | 20% | 降低 LLM 依赖 |
| P95 延迟 | 2000ms | 800ms | 规则快速路径 |
| 用户满意度 | 75% | 90% | 准确性 + 速度 |
| 月度成本 | ¥5000 | ¥1500 | LLM token 成本 |

---

## 附录：代码模板

### 通用 Intent 基类

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class BaseIntent(ABC):
    """通用意图基类"""
    raw_query: str = ""
    confidence: float = 1.0
    extraction_source: str = "rule"  # rule | llm | hybrid
    
    @abstractmethod
    def is_complete(self) -> bool:
        """判断意图是否完整"""
        pass
    
    @abstractmethod
    def to_tool_args(self) -> dict[str, Any]:
        """转换为工具参数"""
        pass
    
    def is_simple(self) -> bool:
        """判断是否为简单查询"""
        # 子类可重写
        return True
```

### 通用 Parser 模板

```python
def parse_intent_generic(
    query: str,
    tool_name: str,
    intent_class: type[BaseIntent]
) -> BaseIntent:
    """通用意图解析模板"""
    # 1. 规则提取
    intent = extract_by_rules(query, tool_name, intent_class)
    
    # 2. 完整性检查
    if intent.is_complete() and intent.confidence > 0.8:
        return intent
    
    # 3. LLM 补全
    intent = complete_by_llm(query, intent, tool_name)
    intent.extraction_source = "hybrid"
    
    return intent
```

### 通用 Processor 链

```python
class ProcessorChain:
    """结果处理器链"""
    
    def __init__(self):
        self.processors: list[ResultProcessor] = []
    
    def register(self, processor: ResultProcessor):
        """注册处理器"""
        self.processors.append(processor)
        self.processors.sort(key=lambda p: p.priority)
    
    def process(
        self,
        results: list[dict],
        intent: BaseIntent
    ) -> list[dict]:
        """执行处理链"""
        for processor in self.processors:
            results = processor.process(results, intent)
        return results
```

---

**文档版本**：v1.0  
**创建日期**：2026-03-03  
**适用范围**：所有工具优化（Location, Weather, Stock, News, Search）  
**维护者**：Kiro AI Assistant
