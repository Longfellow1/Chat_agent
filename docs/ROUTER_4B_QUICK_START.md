# 4B Router 快速开始指南

## 5 分钟快速上手

### 1. 导入和初始化

```python
from agent_service.domain.intents.router_4b_with_logprobs import Router4BWithLogprobs

# 初始化（需要 LLM 客户端）
router = Router4BWithLogprobs(llm_client=your_llm_client)
```

### 2. 路由查询

```python
# 简单查询（规则处理）
result = router.route("我想去北京3天")
# {
#     "success": True,
#     "tool": "plan_trip",
#     "params": {"destination": "北京"},
#     "confidence": 0.9,
#     "needs_clarification": False,
#     "source": "rule"
# }

# 复杂查询（LLM 兜底）
result = router.route("什么是人工智能")
# {
#     "success": True,
#     "tool": "web_search",
#     "params": {"query": "什么是人工智能"},
#     "confidence": 0.82,
#     "needs_clarification": False,
#     "source": "llm"
# }
```

### 3. 处理结果

```python
if result["success"]:
    # 执行工具
    execute_tool(result["tool"], result["params"])
elif result["needs_clarification"]:
    # 触发澄清
    ask_user_for_clarification(result)
else:
    # 处理错误
    show_error(result["error"])
```

## 常见场景

### 场景 1：规则能处理

```python
# 用户："我想去北京3天"
result = router.route("我想去北京3天")

# 规则检测到：目的地（北京）+ 时间（3天）
# 直接返回 plan_trip，无需 LLM 调用
assert result["source"] == "rule"
assert result["tool"] == "plan_trip"
```

### 场景 2：规则无法处理，LLM 兜底

```python
# 用户："我想去一个有山有水的地方"
result = router.route("我想去一个有山有水的地方")

# 规则无法处理（没有明确目的地）
# 调用 LLM 来理解意图
assert result["source"] == "llm"
```

### 场景 3：置信度低，触发澄清

```python
# 用户：模糊查询
result = router.route("帮我规划一下")

# LLM 无法确定意图
# 置信度 < 0.7，触发澄清
if result["needs_clarification"]:
    clarification_prompt = "请问您想去哪里呢？"
```

## 关键参数

### Router 初始化

```python
router = Router4BWithLogprobs(
    llm_client=your_llm_client  # 必需：LLM 客户端
)
```

### 路由结果字段

| 字段 | 类型 | 说明 |
|------|------|------|
| success | bool | 是否成功 |
| tool | str | 工具名称 |
| params | dict | 参数 |
| confidence | float | 置信度（0-1） |
| needs_clarification | bool | 是否需要澄清 |
| source | str | 来源（rule/llm/none/error） |
| error | str | 错误信息 |

### 置信度阈值

```python
# 默认阈值：0.7
# 可以在 LogprobsValidator 中调整

# 高于 0.7：接受结果
# 低于 0.7：触发澄清
```

## 支持的工具

| 工具 | 必需参数 | 示例 |
|------|---------|------|
| plan_trip | destination | "我想去北京3天" |
| find_nearby | city, category | "北京附近有什么好吃的" |
| get_weather | location | "北京的天气怎么样" |
| web_search | query | "什么是人工智能" |
| get_news | query | "最新的新闻" |
| get_stock | symbol | "查询苹果股票" |

## 规则覆盖范围

### 规则 1：plan_trip（目的地 + 时间）

```python
# ✅ 规则能处理
"我想去北京3天"
"上海一周旅游"
"广州5天行程"

# ❌ 规则无法处理
"我想去北京"  # 缺少时间
"去旅游"      # 缺少目的地
```

### 规则 2：find_nearby（位置 + 类别）

```python
# ✅ 规则能处理
"北京附近有什么好吃的"
"上海周边的酒店"
"深圳附近的景点"

# ❌ 规则无法处理
"北京附近"    # 缺少类别
"好吃的"      # 缺少位置
```

### 规则 3：get_weather（天气关键词 + 位置）

```python
# ✅ 规则能处理
"北京的天气怎么样"
"上海今天会下雨吗"
"深圳温度是多少"

# ❌ 规则无法处理
"天气怎么样"  # 缺少位置
"北京"        # 缺少天气关键词
```

## 性能指标

### 延迟

- **规则处理**：< 10ms
- **LLM 处理**：350ms（P50）
- **总体**：350ms（P50）

### 准确率

- **规则准确率**：90%+
- **LLM 准确率**：85%
- **最终成功率**：90%+（包括澄清）

### 成本

- **Token 消耗**：50-100 per query
- **相对成本**：30%（vs 7B）

## 调试技巧

### 1. 检查规则是否命中

```python
from agent_service.domain.intents.router_4b_with_logprobs import RuleBasedRouter

result = RuleBasedRouter.try_route("我想去北京3天")
if result:
    print(f"规则命中：{result.tool}")
else:
    print("规则无法处理，需要 LLM")
```

### 2. 检查置信度

```python
result = router.route(query)
print(f"置信度：{result['confidence']:.2f}")

if result["needs_clarification"]:
    print("置信度低，需要澄清")
```

### 3. 检查来源

```python
result = router.route(query)
print(f"来源：{result['source']}")

# rule：规则处理
# llm：LLM 处理
# none：无 LLM 客户端
# error：处理错误
```

### 4. 记录日志

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
    }
)
```

## 常见问题

### Q: 为什么我的查询没有被规则处理？

**A:** 检查是否满足规则条件：
- plan_trip：需要目的地 + 时间
- find_nearby：需要位置 + 类别
- get_weather：需要天气关键词 + 位置

### Q: 置信度太低怎么办？

**A:** 有几个选项：
1. 降低阈值（0.65-0.7）
2. 优化提示词
3. 添加更多示例

### Q: 如何添加新规则？

**A:** 编辑 `RuleBasedRouter.try_route()` 方法：

```python
# 添加新规则
if condition:
    return ToolCall(
        tool=ToolType.YOUR_TOOL,
        params={"param": value},
        confidence=0.9
    )
```

### Q: 如何优化提示词？

**A:** 编辑 `Router4BWithLogprobs.SYSTEM_PROMPT`：

```python
SYSTEM_PROMPT = """
你的优化后的提示词
...
"""
```

## 相关资源

- **完整文档**：`docs/router_4b_logprobs_integration.md`
- **测试用例**：`tests/unit/test_router_4b_logprobs.py`
- **源代码**：`agent_service/domain/intents/router_4b_with_logprobs.py`
- **实现总结**：`ULTRA_FAST_ROUTER_IMPLEMENTATION_SUMMARY.md`

## 下一步

1. ✅ 理解架构（规则 + LLM 兜底）
2. ✅ 学习基本使用
3. 📍 集成到你的系统
4. 📍 监控关键指标
5. 📍 根据反馈优化

---

**需要帮助？** 查看完整文档或测试用例。
