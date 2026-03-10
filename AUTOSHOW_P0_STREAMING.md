# 车展前P0任务：流式输出实现

**创建时间**: 2026-03-09  
**截止时间**: 车展前3天  
**优先级**: 🔴 P0  
**工作量**: 3-5天

---

## 一、任务目标

实现plan_trip工具的流式输出，满足车展演示需求。

### 验收标准

1. ✅ 支持流式输出（先输出第一天，边生成边播报）
2. ✅ TTFT（首字延迟）≤ 2s
3. ✅ 完整行程生成 ≤ 10s
4. ✅ 车机屏幕呈现效果良好
5. ✅ 标准case和自驾case各通过1条

---

## 二、技术方案

### 2.1 流式输出架构

```
用户查询: "帮我规划上海2日游"
  ↓
[意图识别] plan_trip (规则路由，<10ms)
  ↓
[行程规划引擎]
  ├─ Step 1: 搜索景点 (高德MCP) → 立即返回第一批结果
  ├─ Step 2: 地理聚类 → 流式输出第1天框架
  ├─ Step 3: 规划时段 → 流式输出第1天详情
  ├─ Step 4: 推荐餐厅 → 流式输出第1天餐厅
  ├─ Step 5: 继续第2天 → 流式输出第2天
  └─ Step 6: 完成
  ↓
[流式返回] 边生成边播报
```

### 2.2 实现方式

**方案1: Generator模式（推荐）**

```python
# agent_service/domain/trip/tool.py
async def plan_trip_streaming(
    destination: str,
    days: int = 2,
    travel_mode: str = "transit",
    preferences: list = None,
    amap_client: AmapMCPClient | None = None
):
    """流式输出版本的plan_trip"""
    
    # Step 1: 搜索景点（不流式）
    engine = TripPlannerEngine(amap_client)
    pois = await engine._search_pois(destination, preferences)
    
    # Step 2: 按天聚类
    clusters = engine.clusterer.cluster(pois, days, travel_mode)
    
    # Step 3: 逐天流式输出
    for day_idx, day_pois in enumerate(clusters, 1):
        # 生成当天行程
        day_plan = engine._plan_single_day(day_idx, day_pois, travel_mode)
        
        # 流式输出当天框架
        yield {
            "type": "day_header",
            "day": day_idx,
            "theme": day_plan.theme,
            "text": f"\n第{day_idx}天 - {day_plan.theme}\n"
        }
        
        # 流式输出时段
        for session in day_plan.sessions:
            yield {
                "type": "session",
                "period": session.period,
                "text": f"\n{session.period}\n"
            }
            
            # 流式输出景点
            for stop in session.stops:
                yield {
                    "type": "stop",
                    "name": stop.name,
                    "text": f"• [第{stop.order}站] {stop.name}（{stop.address}）\n"
                }
                
                if stop.transit_to_next:
                    yield {
                        "type": "transit",
                        "text": f"  交通：{stop.transit_to_next.description}\n"
                    }
        
        # 流式输出餐厅推荐
        if day_plan.dinner_recommendations:
            yield {
                "type": "restaurant_header",
                "text": f"\n今日精选餐厅\n"
            }
            
            for restaurant in day_plan.dinner_recommendations:
                yield {
                    "type": "restaurant",
                    "name": restaurant['name'],
                    "text": f"• {restaurant['name']}\n"
                }
    
    # 完成标记
    yield {
        "type": "complete",
        "text": ""
    }
```

**方案2: FastAPI StreamingResponse**

```python
# agent_service/app/api/server.py
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """流式对话接口"""
    
    async def generate():
        # 意图识别
        is_trip, params, _ = route_trip_intent(req.query)
        
        if is_trip and params["destination"]:
            # 流式输出行程
            async for chunk in plan_trip_streaming(
                destination=params["destination"],
                days=params["days"],
                travel_mode=params.get("travel_mode", "transit"),
                preferences=params.get("preferences"),
                amap_client=amap_client
            ):
                # SSE格式
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        else:
            # 非plan_trip，走原有逻辑
            result = await chat_flow.run(req)
            yield f"data: {json.dumps({'type': 'complete', 'text': result.final_text})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### 2.3 延迟优化

**目标**: TTFT ≤ 2s

**优化点**:
1. 景点搜索并行化（如果有多个偏好）
2. 第一天数据优先返回
3. 餐厅推荐异步加载（不阻塞主流程）
4. 缓存热门城市景点数据

```python
# 并行搜索优化
async def _search_pois_parallel(self, destination, preferences):
    """并行搜索多个偏好的POI"""
    if not preferences:
        return await self._search_attractions(destination)
    
    # 并行调用
    tasks = [
        self._search_single_preference(destination, pref)
        for pref in preferences
    ]
    results = await asyncio.gather(*tasks)
    
    # 合并结果
    all_pois = []
    for pois in results:
        all_pois.extend(pois)
    
    return all_pois[:15]  # 取前15个
```

---

## 三、实施步骤

### Day 1: 基础流式框架

- [ ] 创建`plan_trip_streaming()`函数
- [ ] 实现Generator模式
- [ ] 添加FastAPI `/chat/stream`接口
- [ ] 单元测试：验证流式输出格式

### Day 2: 逐天流式输出

- [ ] 实现`_plan_single_day()`方法
- [ ] 按时段流式输出
- [ ] 按景点流式输出
- [ ] 集成测试：验证输出顺序

### Day 3: 延迟优化

- [ ] 并行搜索POI
- [ ] 第一天优先返回
- [ ] 餐厅推荐异步加载
- [ ] 性能测试：TTFT ≤ 2s

### Day 4: 车机适配

- [ ] 确认车机屏幕分辨率
- [ ] 调整输出格式（如需要）
- [ ] 测试车机呈现效果
- [ ] 修复显示问题

### Day 5: 冒烟测试

- [ ] 标准case: "帮我规划上海2日游"
- [ ] 自驾case: "我想自驾游去杭州玩2天"
- [ ] 验证流式输出效果
- [ ] 验证延迟指标
- [ ] 修复发现的问题

---

## 四、测试用例

### 4.1 功能测试

```python
# tests/integration/test_streaming_plan_trip.py

@pytest.mark.asyncio
async def test_streaming_basic():
    """测试基础流式输出"""
    chunks = []
    async for chunk in plan_trip_streaming(
        destination="上海",
        days=2,
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    # 验证输出顺序
    assert chunks[0]["type"] == "day_header"
    assert chunks[0]["day"] == 1
    assert chunks[-1]["type"] == "complete"
    
    # 验证包含必要元素
    types = [c["type"] for c in chunks]
    assert "session" in types
    assert "stop" in types
    assert "restaurant" in types

@pytest.mark.asyncio
async def test_streaming_self_drive():
    """测试自驾模式流式输出"""
    chunks = []
    async for chunk in plan_trip_streaming(
        destination="杭州",
        days=2,
        travel_mode="driving",
        amap_client=amap_client
    ):
        chunks.append(chunk)
    
    # 验证包含驾车交通描述
    transit_chunks = [c for c in chunks if c["type"] == "transit"]
    assert any("驾车" in c["text"] for c in transit_chunks)
```

### 4.2 性能测试

```python
# tests/integration/test_streaming_performance.py

@pytest.mark.asyncio
async def test_ttft_under_2s():
    """测试首字延迟 ≤ 2s"""
    start_time = time.time()
    
    first_chunk = None
    async for chunk in plan_trip_streaming(
        destination="北京",
        days=2,
        amap_client=amap_client
    ):
        if first_chunk is None:
            first_chunk = chunk
            ttft = time.time() - start_time
            break
    
    assert ttft <= 2.0, f"TTFT {ttft:.2f}s 超过2秒"
    print(f"✅ TTFT: {ttft:.2f}s")

@pytest.mark.asyncio
async def test_total_latency_under_10s():
    """测试总延迟 ≤ 10s"""
    start_time = time.time()
    
    chunk_count = 0
    async for chunk in plan_trip_streaming(
        destination="上海",
        days=2,
        amap_client=amap_client
    ):
        chunk_count += 1
    
    total_latency = time.time() - start_time
    
    assert total_latency <= 10.0, f"总延迟 {total_latency:.2f}s 超过10秒"
    print(f"✅ 总延迟: {total_latency:.2f}s")
    print(f"✅ 输出块数: {chunk_count}")
```

---

## 五、车展冒烟测试清单

**执行时间**: 车展前2-3天  
**执行人**: 全员  
**环境**: 车机实际环境

### 测试Case 1: 标准公共交通

```
输入: "帮我规划一个上海2日游"
期望:
  - TTFT ≤ 2s
  - 总延迟 ≤ 10s
  - 流式输出第1天 → 第2天
  - 包含景点、交通、餐厅
  - 车机屏幕显示正常
```

### 测试Case 2: 自驾模式

```
输入: "我想自驾游去杭州玩2天"
期望:
  - TTFT ≤ 2s
  - 总延迟 ≤ 10s
  - 流式输出第1天 → 第2天
  - 交通描述为"驾车X分钟"
  - 车机屏幕显示正常
```

### 验收标准

- [ ] 两个case都通过
- [ ] 延迟指标达标
- [ ] 车机显示效果良好
- [ ] 无明显bug

---

## 六、风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| 高德MCP不稳定 | 中 | 高 | 提前测试，准备Mock数据 |
| 延迟超标 | 中 | 高 | 并行优化，缓存热门城市 |
| 车机显示问题 | 低 | 中 | 提前确认屏幕规格，调整格式 |
| 流式输出bug | 中 | 高 | 充分测试，留出修复窗口 |

---

## 七、交付物

1. ✅ `plan_trip_streaming()` 函数实现
2. ✅ FastAPI `/chat/stream` 接口
3. ✅ 单元测试 + 集成测试
4. ✅ 性能测试报告
5. ✅ 车展冒烟测试报告
6. ✅ 部署文档

---

**状态**: 🔄 进行中  
**负责人**: 后端开发  
**开始时间**: 2026-03-09  
**预计完成**: 2026-03-14
