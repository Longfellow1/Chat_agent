# 统一路由器集成指南

## 架构对比

### 旧架构（两次LLM）
```
用户输入
  ↓
[意图识别LLM] → "plan_trip" (可能错误)
  ↓
[参数提取LLM] → {destination: "北京", days: 3}
  ↓
[工具调用] → 执行
  ↓
问题：
- 两次LLM调用，耗时翻倍
- 意图错误无容错机制
- 参数提取可能不准确
```

### 新架构（单次LLM）
```
用户输入
  ↓
[统一LLM] → {tool: "plan_trip", params: {...}, confidence: 0.95}
  ↓
[参数验证] → 检查必需字段
  ↓
[置信度检查] → 低置信度时fallback
  ↓
[工具调用] → 执行
  ↓
优势：
- 单次LLM调用，快速
- 置信度可控，低置信度自动fallback
- 参数验证失败可提示用户
- 工具执行失败可重试
```

## 使用方式

### 1. 初始化

```python
from agent_service.infra.llm_clients.lm_studio_client import LMStudioClient
from agent_service.domain.intents.unified_router import UnifiedRouter
from agent_service.domain.tools.executor_v2 import ToolExecutorWithRetry

# 初始化LLM客户端
llm_client = LMStudioClient(
    base_url="http://localhost:1234",
    model="qwen3-vl-2b-instruct"
)

# 初始化路由器
router = UnifiedRouter(llm_client)

# 初始化执行器
executor = ToolExecutorWithRetry()
```

### 2. 处理用户查询

```python
def handle_query(query: str):
    # 第1步：路由（单次LLM调用）
    router_result = router.route(query)
    
    if not router_result.success:
        return f"无法理解您的查询: {router_result.error}"
    
    # 第2步：执行（支持容错）
    exec_result = executor.execute_with_retry(
        router_result,
        query=query,
        max_retries=2
    )
    
    if not exec_result.success:
        if exec_result.retry_reason:
            return f"需要更多信息: {exec_result.retry_reason}"
        return f"执行失败: {exec_result.error}"
    
    # 第3步：处理结果
    tool_name = exec_result.tool_used.value
    is_fallback = " (降级)" if exec_result.is_fallback else ""
    
    return {
        "tool": tool_name + is_fallback,
        "result": exec_result.result.text,
        "confidence": router_result.tool_call.confidence
    }
```

### 3. 流式处理

```python
async def handle_query_streaming(query: str):
    # 路由
    router_result = router.route(query)
    
    if not router_result.success:
        yield f"error: {router_result.error}"
        return
    
    # 执行
    exec_result = executor.execute(router_result, query)
    
    if not exec_result.success:
        yield f"error: {exec_result.error}"
        return
    
    # 流式输出结果
    for chunk in exec_result.result.stream():
        yield chunk
```

## 容错机制

### 1. 参数不完整

```python
# 用户查询：「规划一个行程」
# LLM输出：{tool: "plan_trip", params: {}, confidence: 0.6}

result = executor.execute(router_result)
# result.success = False
# result.retry_reason = "请提供更多信息，例如：destination, days"
```

### 2. 置信度低

```python
# 用户查询：「北京怎么样」
# LLM输出：{tool: "encyclopedia", params: {query: "北京"}, confidence: 0.5}

result = executor.execute(router_result)
# 自动降级到 web_search
# result.is_fallback = True
# result.tool_used = ToolType.WEB_SEARCH
```

### 3. 工具执行失败

```python
# 工具调用异常
result = executor.execute_with_retry(router_result, max_retries=2)
# 自动重试，最多2次
```

## 性能对比

| 指标 | 旧架构 | 新架构 | 改进 |
|------|--------|--------|------|
| LLM调用次数 | 2 | 1 | -50% |
| 平均延迟 | ~800ms | ~400ms | -50% |
| 错误恢复 | 无 | 自动fallback | ✓ |
| 参数验证 | 无 | 完整性检查 | ✓ |
| 置信度控制 | 无 | 可配置阈值 | ✓ |

## 配置参数

### 置信度阈值

```python
# 默认：0.7
# 调整：
tool_call.is_confident(threshold=0.8)  # 更严格
tool_call.is_confident(threshold=0.5)  # 更宽松
```

### 重试次数

```python
# 默认：2
executor.execute_with_retry(
    router_result,
    max_retries=3  # 最多重试3次
)
```

### LLM参数

```python
# 在UnifiedRouter.SYSTEM_PROMPT中调整：
# - 置信度评分标准
# - 支持的工具列表
# - 参数提取规则
```

## 迁移步骤

1. **第1阶段**：并行运行新旧架构，对比结果
2. **第2阶段**：逐步切换到新架构（10% → 50% → 100%）
3. **第3阶段**：监控性能和准确率，调整参数
4. **第4阶段**：下线旧架构

## 监控指标

```python
# 需要追踪的指标：
- LLM调用延迟
- 路由准确率（与标注数据对比）
- 置信度分布
- Fallback比例
- 工具执行成功率
- 用户满意度
```

## 常见问题

### Q: 置信度应该设多少？
A: 建议0.7-0.8。太低会导致误判，太高会导致降级过多。

### Q: 参数不完整时怎么办？
A: 返回友好的提示，让用户补充信息。例如：「请告诉我您要去哪个城市？」

### Q: 什么时候应该fallback？
A: 当置信度 < 0.7 且有备选工具时。

### Q: 如何处理多轮对话？
A: 在第二轮及以后，可以使用前一轮的上下文来提高置信度。
