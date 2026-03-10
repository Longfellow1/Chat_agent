# M5.4 plan_trip Milestone 3 规划

## M3目标

完成从用户输入到行程输出的完整链路，包括意图路由、参数提取、MCP Gateway集成。

## M3 P0任务（阻塞上线）

### 1. 交通时间估算修复 ⚠️ **已完成**

**问题严重性**: 
- 用户可见的错误信息（"高铁约3分钟"）
- 影响产品可信度
- 车展演示场景下会直接暴露问题

**解决方案**:
- ✅ 添加`_conservative_estimate()`方法
- ✅ 当POI缺少location/business_area/district/adcode时，返回保守估算
- ✅ 公交："建议预留30分钟"
- ✅ 自驾："建议预留20分钟"

**验证**:
```bash
python test_m5_4_plan_trip_with_llm.py
```

**修改文件**:
- `agent_service/domain/trip/transit_estimator.py`

---

### 2. 意图路由 + 参数提取

**目标**: 从用户查询自动识别plan_trip意图并提取参数

**规则路由信号词**:
- 行程规划: "规划"、"行程"、"安排"、"攻略"
- 旅游: "旅游"、"玩"、"游"、"去XX玩"
- 天数: "X日游"、"X天"、"两天"、"三天"
- 自驾: "自驾"、"开车"、"驾车"

**参数提取**:
- `destination`: 城市名（必需）
- `days`: 天数（默认2）
- `travel_mode`: "transit"或"driving"（默认"transit"）

**LLM兜底**:
- 使用2B intent模型
- 当规则路由无法识别时触发
- 返回意图 + 参数

**实现位置**:
- 新建: `agent_service/domain/intents/trip_router.py`
- 参考: `agent_service/domain/intents/web_search_router.py`

**测试case**:
```python
# 标准case
"帮我规划一个上海2日游"  # destination=上海, days=2, mode=transit
"我想去北京玩两天，帮我安排一下"  # destination=北京, days=2, mode=transit
"自驾去杭州玩2天，有什么推荐"  # destination=杭州, days=2, mode=driving

# 变体case
"上海有什么好玩的，帮我安排3天行程"  # destination=上海, days=3, mode=transit
"开车去苏州玩一天"  # destination=苏州, days=1, mode=driving

# 负例（不应该路由到plan_trip）
"上海到北京怎么走"  # 导航意图，不是行程规划
"上海有什么景点"  # find_nearby意图
"上海天气怎么样"  # get_weather意图
```

---

### 3. MCP Gateway集成

**目标**: 修改`_trip()`方法，调用新的plan_trip工具

**修改文件**: `agent_service/infra/tool_clients/mcp_gateway.py`

**关键问题**: `invoke()`是同步方法，但`plan_trip()`是async函数

**解决方案**: 
1. 保持`invoke()`同步接口（不破坏现有调用）
2. 在`_trip()`内部使用`asyncio.run()`调用async函数
3. 添加event loop检测，避免"already running"错误

**修改内容**:
```python
def _trip(self, destination: str, days: int = 2, travel_mode: str = "transit") -> ToolResult:
    """Plan trip using new trip planner engine."""
    if not destination:
        return ToolResult(ok=False, text="缺少目的地", error="missing_destination")
    
    # Import here to avoid circular dependency
    from domain.trip.tool import plan_trip
    import asyncio
    
    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
        # Already in async context - cannot use asyncio.run()
        # This should not happen in current architecture, but handle it gracefully
        return ToolResult(
            ok=False,
            text="行程规划功能暂时不可用",
            error="async_context_conflict"
        )
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        pass
    
    # Call async plan_trip
    result = asyncio.run(plan_trip(
        destination=destination,
        days=days,
        travel_mode=travel_mode,
        amap_client=self.amap_mcp
    ))
    
    # Apply LLM post-processing if result is ok
    if result.ok:
        result = self._apply_llm_rewrite(result, destination, days, travel_mode)
    
    return result

def _apply_llm_rewrite(self, result: ToolResult, destination: str, days: int, travel_mode: str) -> ToolResult:
    """Apply LLM rewriting to trip result."""
    try:
        from infra.llm_clients.lm_studio_client import LMStudioClient
        import logging
        
        logger = logging.getLogger(__name__)
        llm = LMStudioClient()
        
        system_prompt = """你是一个专业的旅游规划助手。你的任务是将结构化的行程信息重写为自然、友好、易读的文本。

要求：
1. 保持所有景点、地址、交通信息完整
2. 使用自然流畅的语言
3. 添加适当的过渡和连接词
4. 保持专业但友好的语气
5. 不要添加原文中没有的信息
6. 输出长度控制在800字以内
7. 直接输出重写后的文本，不要输出思考过程"""

        user_prompt = f"""用户查询: {destination}{days}日游

工具返回的原始行程信息:
{result.text}

请将上述行程信息重写为自然、友好的文本，让用户更容易理解和使用。"""

        rewritten_text = llm.generate(
            user_query=user_prompt,
            system_prompt=system_prompt
        )
        
        # Update result with rewritten text
        result.text = rewritten_text
        
        # Add rewrite metadata
        if result.raw is None:
            result.raw = {}
        result.raw["llm_rewritten"] = True
        
        return result
        
    except Exception as e:
        # If LLM fails, return original result
        logger.warning(f"LLM rewrite failed: {e}, using original output")
        return result
```

**关键点**:
1. 使用`asyncio.get_running_loop()`检测是否已在async上下文
2. 如果已在async上下文，返回错误（当前架构不应该发生）
3. 如果不在async上下文，安全使用`asyncio.run()`
4. 添加详细的错误处理和日志

---

### 4. 完整端到端测试

**目标**: 验证从用户查询到最终输出的完整链路

**测试文件**: `tests/integration/test_m5_4_plan_trip_m3.py`

**测试case**:

1. **标准case** (5条)
   - "帮我规划一个上海2日游"
   - "我想去北京玩两天，帮我安排一下"
   - "自驾去杭州玩2天，有什么推荐"
   - "上海有什么好玩的，帮我安排3天行程"
   - "开车去苏州玩一天"

2. **自驾vs公交对照** (5对，共10条)
   - "上海2日游" vs "自驾上海2日游"
   - "北京3天行程" vs "开车去北京玩3天"
   - "杭州旅游攻略" vs "驾车杭州旅游"
   - "苏州一日游" vs "自驾苏州一日游"
   - "南京两天怎么玩" vs "开车去南京玩两天"

3. **负例** (8条，应该不路由到plan_trip)
   - "上海到北京怎么走" → 应该拒绝或路由到其他工具（导航意图）
   - "上海有什么景点" → find_nearby
   - "上海天气怎么样" → get_weather
   - "上海附近的餐厅" → find_nearby
   - "上海最新新闻" → get_news
   - "帮我规划一下" → 应该触发澄清（无目的地）
   - "帮我规划一个行程" → 应该触发澄清（无目的地）
   - "打开行程规划" → 应该拒绝（操作指令）

**验收标准**:
- 意图识别准确率: ≥90% (18/20标准case + 对照case)
- 负例拒绝率: 100% (8/8)
- 参数提取准确率: 100% (destination, days, travel_mode)
- LLM输出质量: 自然流畅，保留所有信息
- 交通时间描述: 无错误信息（"高铁约3分钟"等）

---

## M3 P1任务（优化）

### 1. 使用maps_geo补全location

**目标**: 提高交通时间估算准确性

**方案**:
- 当POI缺少location字段时，调用`maps_geo`获取经纬度
- 使用真实经纬度计算距离
- 提高估算准确性

**实现位置**:
- `agent_service/domain/trip/engine.py` - `_search_attractions()`方法

**优先级**: P1（M3完成后再优化）

---

### 2. 使用maps_place_detail获取完整POI信息

**目标**: 补全business_area、district、adcode等字段

**方案**:
- 对每个POI调用`maps_place_detail`获取完整信息
- 补全缺失字段
- 提高聚类和估算准确性

**实现位置**:
- `agent_service/domain/trip/engine.py` - `_search_attractions()`方法

**优先级**: P1（M3完成后再优化）

---

## 验收标准

### M3 P0验收标准

| 标准 | 目标 | 验收方式 |
|------|------|----------|
| 交通时间修复 | 无错误信息 | 运行测试，检查输出 |
| 意图路由准确率 | ≥90% | 20条标准case + 对照case |
| 负例拒绝率 | 100% | 8条负例（含无目的地+操作指令） |
| 参数提取准确率 | 100% | 检查destination, days, travel_mode |
| LLM输出质量 | 自然流畅 | 人工评估 |
| MCP Gateway集成 | 完整链路打通 | 端到端测试 |
| asyncio.run()安全性 | 无event loop冲突 | 集成测试 |

### M3完成标志

- ✅ 交通时间修复完成
- ⬜ 意图路由 + 参数提取实现
- ⬜ MCP Gateway集成完成
- ⬜ 端到端测试通过（20条标准case + 5条负例）
- ⬜ 验收标准全部达标

---

## 文件清单

### 需要新建的文件
- `agent_service/domain/intents/trip_router.py` - 意图路由
- `tests/integration/test_m5_4_plan_trip_m3.py` - M3端到端测试

### 需要修改的文件
- ✅ `agent_service/domain/trip/transit_estimator.py` - 交通时间修复
- ⬜ `agent_service/infra/tool_clients/mcp_gateway.py` - 集成新工具
- ✅ `agent_service/infra/llm_clients/lm_studio_client.py` - 模型选型文档化

### 参考文件
- `agent_service/domain/intents/web_search_router.py` - 意图路由参考
- `agent_service/domain/location/parser.py` - 参数提取参考
- `test_m5_4_plan_trip_with_llm.py` - LLM后处理参考

---

## 关键决策记录

### 1. 交通时间问题提升到P0

**原因**:
- 用户可见的错误信息
- 影响产品可信度
- 车展演示场景下会直接暴露

**解决方案**:
- 添加保守估算逻辑
- 当数据不足时，返回"建议预留X分钟"
- 避免输出错误数字

### 2. asyncio.run()风险处理

**问题**: `mcp_gateway.invoke()`是同步方法，但`plan_trip()`是async函数

**风险**: 如果`invoke()`在async上下文中被调用，`asyncio.run()`会抛出`RuntimeError: This event loop is already running`

**解决方案**:
- 添加event loop检测
- 如果已在async上下文，返回错误（当前架构不应该发生）
- 如果不在async上下文，安全使用`asyncio.run()`

**文档化位置**:
- `agent_service/infra/tool_clients/mcp_gateway.py` - `_trip()`方法注释
- 避免生产环境event loop冲突

### 3. 负例测试集扩充

**原因**: 
- 真实流量中发现的高频边界case
- 无目的地截断："帮我规划一下"、"帮我规划一个行程"
- 操作指令："打开行程规划"、"规划功能在哪里"

**测试case**:
- 无目的地: 应该触发澄清，不能路由到plan_trip
- 操作指令: 应该拒绝，不是行程规划意图

**负例数量**: 从5条扩到8条

---

## 时间估算

- 意图路由 + 参数提取: 2-3小时
- MCP Gateway集成: 1-2小时
- 端到端测试: 2-3小时
- 调试 + 优化: 1-2小时

**总计**: 6-10小时

---

**创建时间**: 2026-03-09  
**状态**: M3规划完成，等待执行
