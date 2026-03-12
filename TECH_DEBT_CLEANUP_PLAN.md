# 技术债清理计划 - 今日完成

## 反思：三层架构问题的根因

### 问题 1：评测链路和业务链路混淆

**根因**：`tool_status=ok` 同时表示"链路成功"和"结果可信"

**影响**：
- Mock 返回 → tool_status=ok → 评测 PASS（假阳性）
- LLM 兜底 → tool_status=ok → 评测 PASS（质量未知）
- 真实工具 → tool_status=ok → 评测 PASS（真阳性）

**后果**：30 条 Mock 假 PASS，评测数字不可信

### 问题 2：mcp_gateway.py 职责过载（882 行）

**根因**：单文件承担 5 个职责

**影响**：
- 修 Bing MCP → 动 gateway
- 修城市提取 → 动 planner
- 两个 Planner 并存，功能重复

**后果**：改动成本高，bug 传播快

### 问题 3：规则优先级隐式化

**根因**：优先级写在 if-else 顺序里

**影响**：
- "广州旅游" bug（规则2 覆盖了旅游意图）
- 加规则不知道插在哪
- 冲突检测靠人工

**后果**：规则维护成本高，易出错

---

## 今日清理计划（3 小时）

### 优先级 1：评测链路隔离（1 小时）✅ 必做

**目标**：分离 `tool_status` 和 `result_quality`

**改动**：
1. 在返回结果中添加 `result_quality` 字段
2. 评测脚本只统计 `result_quality=real` 的 case
3. 其他来源单独统计降级率

**文件**：
- `agent_service/infra/tool_clients/mcp_gateway.py`（添加 result_quality）
- `scripts/run_full_eval.py`（修改评测逻辑）

**验证**：
- 重跑 100 条评测，确认 Mock case 不计入准确率
- 输出降级率统计

**收益**：
- 评测数字可信
- 降级率可监控
- 后续评测不需要人工核查

---

### 优先级 2：规则优先级显式化（1 小时）✅ 必做

**目标**：规则优先级从代码逻辑提取到配置表

**改动**：
1. 创建 `RULE_PRIORITY` 配置表
2. 规则按优先级排序执行
3. 添加规则冲突检测

**文件**：
- `agent_service/domain/intents/router_4b_with_logprobs.py`

**实现**：
```python
# 显式优先级表
RULE_PRIORITY = [
    (0, "trip_intent_keywords", ToolType.PLAN_TRIP, 
     lambda q: any(kw in q for kw in TRIP_KEYWORDS)),
    
    (1, "weather_keywords", ToolType.GET_WEATHER,
     lambda q: any(kw in q for kw in ["天气", "温度", "下雨"])),
    
    (2, "location_category", ToolType.FIND_NEARBY,
     lambda q: _extract_destination(q) and _extract_category(q)),
    
    (3, "destination_time", ToolType.PLAN_TRIP,
     lambda q: _extract_destination(q) and _has_time(q)),
]

def try_route(query: str) -> Optional[ToolCall]:
    """按优先级顺序匹配规则"""
    for priority, name, tool, matcher in RULE_PRIORITY:
        if matcher(query):
            return ToolCall(tool=tool, ...)
    return None
```

**验证**：
- 运行 60 条 trace 测试
- 确认规则命中率不变
- 确认无冲突

**收益**：
- 规则优先级可见
- 加规则时明确插入位置
- 冲突可自动检测

---

### 优先级 3：mcp_gateway 职责拆分（1 小时）⚠️ 可选

**目标**：拆分 gateway 的 5 个职责

**改动**：
1. 创建 `tool_executor.py`（工具调用）
2. 创建 `fallback_chain.py`（降级链路）
3. gateway 只保留路由决策

**文件**：
- 新建 `agent_service/domain/tools/tool_executor.py`
- 新建 `agent_service/domain/tools/fallback_chain.py`
- 重构 `agent_service/infra/tool_clients/mcp_gateway.py`

**风险**：
- 改动范围大（882 行）
- 可能影响现有功能
- 需要完整回归测试

**建议**：
- 今天只做设计，不动代码
- 明天专门排期重构
- 车展后再做

---

## 执行顺序

### 第一步：评测链路隔离（30 分钟）

1. 添加 `result_quality` 字段
2. 修改评测脚本统计逻辑
3. 重跑 100 条验证

### 第二步：规则优先级显式化（30 分钟）

1. 创建 `RULE_PRIORITY` 表
2. 重构 `try_route` 方法
3. 运行 60 条 trace 验证

### 第三步：文档和总结（30 分钟）

1. 更新架构文档
2. 记录改动和验证结果
3. 输出技术债清理报告

---

## 验证标准

### 评测链路隔离

- [ ] `result_quality` 字段已添加
- [ ] 评测脚本只统计 `real` 结果
- [ ] 降级率单独输出
- [ ] 100 条评测数字正确

### 规则优先级显式化

- [ ] `RULE_PRIORITY` 表已创建
- [ ] 规则按优先级执行
- [ ] 60 条 trace 测试通过
- [ ] 规则命中率不变

---

## 不做的事（明确边界）

### 今天不做

1. ❌ mcp_gateway 重构（风险大，排期明天）
2. ❌ 两个 Planner 合并（需求不明确）
3. ❌ 新增规则（先把架构理顺）
4. ❌ 性能优化（功能优先）

### 为什么不做

- mcp_gateway 重构：882 行，改动风险大，需要完整回归
- Planner 合并：需要先理清两个 Planner 的差异
- 新增规则：架构理顺后再加，避免重复劳动

---

## 预期收益

### 短期（今天）

- 评测数字可信（无 Mock 污染）
- 规则优先级清晰（无隐式依赖）
- 技术债可见（降级率监控）

### 中期（本周）

- 加规则成本降低（显式优先级）
- 评测效率提升（无需人工核查）
- 代码可维护性提升

### 长期（车展后）

- gateway 重构完成（职责清晰）
- Planner 合并完成（无重复代码）
- 架构健康度提升

---

## 风险和应对

### 风险 1：改动影响现有功能

**应对**：
- 每个改动后立即运行测试
- 保留原有代码（注释，不删除）
- 出问题立即回滚

### 风险 2：时间不够

**应对**：
- 优先级 1 必做（评测链路）
- 优先级 2 必做（规则优先级）
- 优先级 3 可延后（gateway 重构）

### 风险 3：验证不充分

**应对**：
- 每个改动都有验证标准
- 运行现有测试套件
- 输出前后对比数据

---

## 开始执行

现在开始执行优先级 1 和 2，预计 2 小时完成。

**时间安排**：
- 14:00-14:30 评测链路隔离
- 14:30-15:00 规则优先级显式化
- 15:00-15:30 验证和文档

**输出**：
- 代码改动（2 个文件）
- 验证结果（测试通过）
- 技术债清理报告
