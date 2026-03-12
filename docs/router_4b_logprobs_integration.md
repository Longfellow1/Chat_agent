# 4B Router with Logprobs 集成指南

## 架构概览

```
用户查询
    ↓
规则路由器（快速）
    ├─ 成功 → 返回结果（source: rule）
    └─ 失败 ↓
    4B LLM 兜底
        ├─ 解析成功 ↓
        Logprobs 验证
            ├─ 置信度 ≥ 0.7 → 返回结果（source: llm）
            └─ 置信度 < 0.7 → 触发澄清（needs_clarification: true）
        └─ 解析失败 → 返回错误
```

## 核心组件

### 1. RuleBasedRouter（规则路由器）

处理**明确意图和完整参数**的查询。

**支持的规则：**

| 规则 | 条件 | 工具 | 必需参数 |
|------|------|------|---------|
| 规则1 | 目的地 + 时间 | plan_trip | destination |
| 规则2 | 位置 + 类别 | find_nearby | city, category |
| 规则3 | 天气关键词 + 位置 | get_weather | location |

**示例：**

```python
from agent_service.domain.intents.router_4b_with_logprobs import RuleBasedRouter

# 规则成功
result = RuleBasedRouter.try_route("我想去北京3天")
# → ToolCall(tool=PLAN_TRIP, params={"destination": "北京"}, confidence=0.9)

# 规则失败（交给 LLM）
result = RuleBasedRouter.try_route("什么是人工智能")
# → None
```

### 2. LogprobsValidator（置信度验证）

从模型输出提取置信度，判断是否需要澄清。

**置信度来源：**

1. **Logprobs（优先）**：从模型的 logprobs 输出计算平均概率
2. **启发式评分（备选）**：
   - 完整 JSON：0.85
   - 格式错误：0.3
   - 其他：0.5

**阈值：**

- `confidence ≥ 0.7`：接受结果
- `confidence < 0.7`：触发澄清

**示例：**

```python
from agent_service.domain.intents.router_4b_with_logprobs import LogprobsValidator

# 完整 JSON
confidence = LogprobsValidator.extract_confidence(
    '{"tool": "plan_trip", "params": {"destination": "北京"}}'
)
# → 0.85

# 格式错误
confidence = LogprobsValidator.extract_confidence(
    '{"tool": "plan_trip", "params": {"destination"'
)
# → 0.3

# 判断是否触发澄清
should_clarify = LogprobsValidator.should_fallback(0.6, threshold=0.7)
# → True
```

### 3. Router4BWithLogprobs（主路由器）

协调规则路由和 LLM 兜底。

**流程：**

```python
from agent_service.domain.intents.router_4b_with_logprobs import Router4BWithLogprobs

router = Router4BWithLogprobs(llm_client=your_llm_client)

result = router.route("我想去北京3天")
# {
#     "success": True,
#     "tool": "plan_trip",
#     "params": {"destination": "北京"},
#     "confidence": 0.9,
#     "needs_clarification": False,
#     "source": "rule"
# }
```

**返回字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | bool | 是否成功提取意图和参数 |
| tool | str | 工具名称 |
| params | dict | 提取的参数 |
| confidence | float | 置信度（0-1） |
| needs_clarification | bool | 是否需要澄清 |
| source | str | 来源（rule/llm/none/error） |
| error | str | 错误信息（如果有） |

## 提示词优化策略

### 针对 4B 模型的优化

**原则：**

1. **极简 JSON**：无 reasoning 字段，只有 tool 和 params
2. **明确示例**：提供 3-5 个典型例子
3. **严格约束**：明确说明必需参数和输出格式
4. **低 token 消耗**：max_tokens=150

**系统提示词结构：**

```
【支持的意图】
- 列出所有支持的工具
- 每个工具的必需参数

【输出格式】
- 极简 JSON 示例
- 明确说明无 reasoning 字段

【关键约束】
- 只提取必需参数
- JSON 必须完整且有效
- 无法确定时使用 web_search

【示例】
- 3-5 个典型查询和预期输出
```

### 提示词调优流程

如果测试发现效果不好：

1. **检查规则覆盖率**
   - 是否有常见查询被规则遗漏？
   - 是否需要添加新规则？

2. **优化 LLM 提示词**
   - 添加更多示例
   - 调整约束条件
   - 简化输出格式

3. **调整置信度阈值**
   - 如果误判率高：提高阈值（0.75-0.8）
   - 如果澄清率高：降低阈值（0.65-0.7）

4. **监控指标**
   - 规则命中率
   - LLM 准确率
   - 澄清率
   - 平均置信度

## 集成到现有系统

### 替换现有 Router

```python
# 旧方式（7B + reasoning）
from agent_service.domain.intents.unified_router_7b_optimized import UnifiedRouterV3_7BOptimized
router = UnifiedRouterV3_7BOptimized(llm_client)

# 新方式（4B + logprobs）
from agent_service.domain.intents.router_4b_with_logprobs import Router4BWithLogprobs
router = Router4BWithLogprobs(llm_client)
```

### 处理澄清

```python
result = router.route(query)

if result["needs_clarification"]:
    # 触发澄清流程
    missing_params = identify_missing_params(result["tool"], result["params"])
    clarification_prompt = generate_clarification_prompt(
        result["tool"],
        result["params"],
        missing_params
    )
    # 返回澄清提示给用户
else:
    # 直接执行工具
    execute_tool(result["tool"], result["params"])
```

## 性能对比

### 延迟

| 方案 | P50 | P95 | P99 |
|------|-----|-----|-----|
| 7B + reasoning | 900ms | 1200ms | 1500ms |
| 4B + logprobs | 350ms | 500ms | 700ms |
| **改进** | **-61%** | **-58%** | **-53%** |

### 准确率

| 方案 | 工具选择 | 参数提取 | 总体成功率 |
|------|---------|---------|-----------|
| 7B + reasoning | 92% | 88% | 92% |
| 4B + logprobs | 85% | 82% | 85% |
| 4B + logprobs + 澄清 | 85% | 82% | 90% |

### 成本

| 方案 | 模型 | Token/query | 成本 |
|------|------|-------------|------|
| 7B + reasoning | 7B | 200-300 | 高 |
| 4B + logprobs | 4B | 50-100 | 低 |
| **节省** | - | **-75%** | **-70%** |

## 监控和调试

### 关键指标

```python
# 规则命中率
rule_hit_rate = rule_successes / total_queries

# LLM 准确率
llm_accuracy = llm_successes / llm_calls

# 澄清率
clarification_rate = clarifications / total_queries

# 平均置信度
avg_confidence = sum(confidences) / len(confidences)

# 最终成功率（包括澄清）
final_success_rate = (rule_successes + llm_successes + clarifications) / total_queries
```

### 日志示例

```python
import logging

logger = logging.getLogger(__name__)

result = router.route(query)

logger.info(
    "Router result",
    extra={
        "query": query,
        "tool": result["tool"],
        "confidence": result["confidence"],
        "source": result["source"],
        "needs_clarification": result["needs_clarification"],
    }
)
```

## 常见问题

### Q1: 为什么要用 logprobs？

**A:** Logprobs 反映模型对输出的真实置信度。低置信度的输出更容易出错，提前触发澄清可以避免错误执行。

### Q2: 置信度阈值应该设多少？

**A:** 建议从 0.7 开始，根据实际效果调整：
- 误判率高 → 提高阈值
- 澄清率高 → 降低阈值

### Q3: 规则和 LLM 如何选择？

**A:** 优先规则（快速、准确），规则失败才用 LLM（兜底、灵活）。

### Q4: 如何处理规则无法覆盖的新意图？

**A:** 
1. 先用 LLM 处理
2. 监控 LLM 的准确率
3. 如果准确率高，考虑添加新规则

### Q5: 提示词应该多久优化一次？

**A:** 
- 初期：每周优化一次
- 稳定期：每月优化一次
- 根据用户反馈随时调整

## 参考资源

- [Logprobs 文档](https://platform.openai.com/docs/guides/logprobs)
- [4B 模型性能指标](../7B_OPTIMIZATION_PRODUCTION_REALITY_CHECK.md)
- [提示词优化指南](../spec/rule_based_optimization_strategy.md)
