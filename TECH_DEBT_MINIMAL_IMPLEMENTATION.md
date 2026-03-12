# 技术债最小化实施方案

## 当前状态分析

经过代码检查，发现：

1. **评测链路问题**：
   - `tool_status` 在 `chat_flow.py` 中设置为 "ok" 或 "fallback_or_error"
   - 评测脚本 `run_full_eval.py` 检查 `tool_status in {"ok", "missing_slots"}`
   - 问题：fallback 也返回 "ok"，导致假 PASS

2. **规则优先级问题**：
   - `router_4b_with_logprobs.py` 中规则顺序隐式
   - 已经修复了"广州旅游" bug（规则0 优先级最高）
   - 但优先级仍然隐式

## 最小化方案（2 小时内完成）

### 方案 1：评测链路隔离（最小改动）

**不改业务代码**，只改评测脚本：

```python
# scripts/run_full_eval.py

# 添加结果来源检测
def detect_result_quality(result) -> str:
    """检测结果来源质量"""
    
    # 检查是否是 Mock
    if "mock" in str(result.raw).lower():
        return "mock"
    
    # 检查是否是 LLM 兜底
    if result.tool_provider == "llm_fallback":
        return "fallback_llm"
    
    # 检查是否是搜索兜底
    if "fallback" in result.tool_provider.lower():
        return "fallback_search"
    
    # 真实工具返回
    return "real"

# 修改统计逻辑
def evaluate_case(case, result):
    quality = detect_result_quality(result)
    
    # 只有 real 结果才计入准确率
    if quality == "real":
        return {"pass": result.correct, "quality": "real"}
    else:
        return {"pass": False, "quality": quality, "note": "降级结果不计入准确率"}
```

**优点**：
- 不动业务代码，风险为 0
- 立即可用
- 评测数字立即可信

**缺点**：
- 检测逻辑启发式，可能不准
- 无法从根源解决问题

### 方案 2：规则优先级显式化（最小改动）

**只加注释和文档**，不改代码结构：

```python
# agent_service/domain/intents/router_4b_with_logprobs.py

class RuleBasedRouter:
    """
    规则路由器（处理简单 query）
    
    规则优先级（从高到低）：
    0. 旅游意图关键词 → plan_trip（最高优先级）
    1. 目的地 + 时间 → plan_trip
    2. 位置 + 类别 → find_nearby
    3. 天气关键词 + 位置 → get_weather
    
    注意：规则按顺序匹配，先匹配到的优先
    """
    
    @staticmethod
    def try_route(query: str) -> Optional[ToolCall]:
        """
        尝试用规则路由
        
        规则按优先级顺序执行，先匹配到的返回
        """
        
        # 规则0：旅游意图关键词（优先级最高）
        # 修复 bug：「广州旅游」应该走 plan_trip，不是 find_nearby
        if any(kw in query for kw in RuleBasedRouter.TRIP_KEYWORDS):
            ...
        
        # 规则1：目的地 + 时间 = plan_trip
        ...
        
        # 规则2：位置 + 类别 = find_nearby
        # 注意：这个规则优先级低于旅游意图
        ...
        
        # 规则3：天气关键词 = get_weather
        ...
```

**优点**：
- 不改代码逻辑，风险为 0
- 优先级可见
- 后续加规则有文档参考

**缺点**：
- 没有自动冲突检测
- 仍然是隐式优先级

---

## 今日执行计划（修正版）

### 第一步：评测链路隔离（30 分钟）

1. 在 `run_full_eval.py` 添加 `detect_result_quality` 函数
2. 修改统计逻辑，只统计 `real` 结果
3. 输出降级率统计
4. 重跑 100 条验证

### 第二步：规则优先级文档化（15 分钟）

1. 在 `router_4b_with_logprobs.py` 添加优先级注释
2. 在每个规则前添加优先级说明
3. 更新类文档字符串

### 第三步：验证和总结（15 分钟）

1. 运行测试确认无破坏
2. 输出技术债清理报告
3. 记录后续优化方向

---

## 后续优化方向（车展后）

### 评测链路彻底隔离

在业务代码中添加 `result_quality` 字段：

```python
# agent_service/app/orchestrator/chat_flow.py

tool_status="ok" if tool_result.ok else "fallback_or_error",
result_quality="real" if is_real_tool else "fallback",  # 新增
```

### 规则优先级显式化

创建 `RULE_PRIORITY` 配置表，自动冲突检测

### mcp_gateway 职责拆分

拆分为 router、executor、fallback、formatter 四个模块

---

## 开始执行

现在执行最小化方案，预计 1 小时完成。
