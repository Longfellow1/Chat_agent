# 技术债清理完成报告

## 执行时间
2026-03-11

## 完成任务

### 任务1：规则优先级文档化 ✅

**文件**: `agent_service/domain/intents/router_4b_with_logprobs.py`

**改动内容**:
1. 在 `RuleBasedRouter` 类文档字符串添加完整的规则优先级说明
2. 在 `try_route` 方法添加规则执行顺序注释
3. 在每个规则前添加优先级标记和说明

**规则优先级**:
```
优先级 0（最高）：旅游意图关键词 → plan_trip
优先级 1：目的地 + 时间 → plan_trip
优先级 2：位置 + 类别 → find_nearby
优先级 3：天气关键词 → get_weather
```

**冲突处理示例**:
- "广州旅游" 同时匹配规则0（旅游）和规则2（位置+类别）
- 解决：规则0 优先级更高，返回 plan_trip

**耗时**: 15分钟
**风险**: 零（仅添加注释）

---

### 任务2：评测链路隔离 - 添加 result_quality 字段 ✅

#### 2.1 业务代码改动

**文件1**: `agent_service/app/schemas/contracts.py`
- 在 `ChatResponse` 添加 `result_quality` 字段
- 类型: `str = "none"`
- 可选值: `"real"` | `"fallback_llm"` | `"fallback_search"` | `"rule"` | `"none"`

**文件2**: `agent_service/app/orchestrator/chat_flow.py`
- 添加 `_infer_result_quality()` 函数，根据以下逻辑推断质量:
  1. 如果 `route_source == "rule"` → `"rule"`
  2. 如果 `tool_status != "ok"` → `"none"`
  3. 如果 `fallback_chain` 非空 → 根据 provider 判断 `"fallback_llm"` 或 `"fallback_search"`
  4. 如果 provider 包含 "fallback" → 根据是否包含 "llm" 判断
  5. 默认 → `"real"`

- 在创建 `ChatResponse` 时调用 `_infer_result_quality()` 设置 `result_quality` 字段

#### 2.2 评测脚本改动

**文件**: `scripts/run_full_eval.py`

**改动1**: `generate_statistics()` 函数
- 添加 `quality_breakdown` 统计（按 result_quality 分组）
- 添加 `honest_accuracy` 计算（只统计 real + rule）
- 添加 `fallback_rate` 计算（fallback_llm + fallback_search 占比）

**改动2**: `print_summary()` 函数
- 输出 `Honest Accuracy (real+rule only)`
- 输出 `Fallback Rate`
- 输出 `Result Quality Breakdown` 详细统计

**耗时**: 45分钟
**风险**: 极低（业务逻辑不变，只添加元数据）

---

## 关键设计决策

### 为什么不用延迟推断 result_quality？

**原方案（被否决）**:
```python
if total_latency < 10:  # 规则命中通常 < 10ms
    return "rule"
```

**问题**:
1. 用副作用推断原因，脆弱
2. 规则层加字典查询后延迟可能变成 15ms，判断失效
3. LLM 缓存命中时也可能 < 10ms，误判为 rule

**正确方案**:
- 质量信息由业务代码明确输出（`result_quality` 字段）
- 评测脚本直接读取，不用猜
- 数据可信度本质上不同

### 为什么不预估准确率？

**原方案（被否决）**:
```
修复后预计 75-80%
```

**问题**:
- 数字没有任何数据支撑，是凭感觉估的
- 写进报告会被当成承诺，实际跑出来不一样又要解释

**正确方案**:
```
实施后以实际运行数据为准
```

---

## 验证方式

### 验证1：规则优先级文档
```bash
# 检查注释是否添加
grep -A 20 "规则优先级" agent_service/domain/intents/router_4b_with_logprobs.py
```

### 验证2：result_quality 字段
```bash
# 检查 ChatResponse 是否有 result_quality 字段
grep "result_quality" agent_service/app/schemas/contracts.py

# 检查 _infer_result_quality 函数是否存在
grep "def _infer_result_quality" agent_service/app/orchestrator/chat_flow.py
```

### 验证3：评测脚本统计
```bash
# 运行评测，检查输出是否包含新字段
python scripts/run_full_eval.py --limit 10

# 预期输出包含:
# - Honest Accuracy (real+rule only): XX%
# - Fallback Rate: XX%
# - Result Quality Breakdown:
#   - real: X/X (XX%)
#   - fallback_llm: X/X (XX%)
#   - fallback_search: X/X (XX%)
#   - rule: X/X (XX%)
```

---

## 后续工作（车展后）

### 优化1：评测链路彻底隔离
在 `mcp_gateway.py` 的 `ToolResult` 添加 `result_quality` 字段，从源头标记质量。

### 优化2：规则优先级显式化
创建 `RULE_PRIORITY` 配置表，自动冲突检测。

### 优化3：mcp_gateway 职责拆分
拆分为 router、executor、fallback、formatter 四个模块。

---

## 总结

✅ 规则优先级文档化完成（15分钟）
✅ result_quality 字段添加完成（45分钟）
✅ 评测脚本统计增强完成（15分钟）

**总耗时**: 75分钟
**风险**: 极低（不动核心业务逻辑）
**收益**: 
- 数据可信（诚实准确率 vs 表面准确率）
- 代码可维护（规则优先级清晰）
- 问题可见化（降级率统计）
