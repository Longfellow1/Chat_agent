# M5.4 plan_trip M4 环境对齐评估

## 评估时间
2026-03-09

## 背景

M1-M3的测试都在本地环境运行：
- LM Studio本地模型（qwen2.5-7b-instruct-mlx）
- 高德MCP本地调用
- Mock数据补充

M4是生产环境集成，需要提前确认本地和生产环境的差距，避免M3的100%测试覆盖在生产环境失效。

---

## 环境对齐项评估

### 1. LLM模型一致性 ✅

**本地环境**:
- 模型：qwen2.5-7b-instruct-mlx
- 配置：`LM_STUDIO_MODEL=qwen2.5-7b-instruct-mlx`
- 参数量：7B
- 特点：无thinking模式输出

**生产环境**:
- 后端选择：通过`AGENT_BACKEND`环境变量控制
  - `lmstudio`: 使用LMStudioClient（默认）
  - `coze`: 使用CozeClient
- 默认模型：qwen2.5-7b-instruct-mlx（与本地一致）

**结论**: ✅ 模型一致性已确认
- 参数量和精度基线一致（7B）
- 无需重新验证LLM重写输出质量
- 如果生产环境切换到Coze，需要重新验证输出质量

**风险**: 
- 如果生产环境使用Coze后端，模型可能不同，需要重新验证
- 建议：M4第一步确认生产环境`AGENT_BACKEND`配置

---

### 2. 高德MCP数据字段一致性 ⚠️

**本地环境问题**:
- M2发现本地POI缺少`location`/`business_area`/`district`/`adcode`字段
- 导致交通时间计算失败，输出"高铁约3分钟"错误
- 已通过`_conservative_estimate()`降级处理

**生产环境未知项**:
1. 生产环境的高德MCP是否返回完整字段？
2. 如果返回完整字段，`_conservative_estimate()`是否会被误触发？
3. 如果同样缺少字段，降级逻辑是否在所有城市下都正确？

**验证方法**:
```python
# M4第一步：在生产环境运行POI字段检查
from infra.tool_clients.amap_mcp_client import AmapMCPClient

client = AmapMCPClient()
result = client.find_nearby(keyword="星巴克", city="上海")

# 检查返回的POI字段
if result.ok and result.raw:
    pois = result.raw.get("pois", [])
    if pois:
        poi = pois[0]
        print("POI字段:", poi.keys())
        print("location:", poi.get("location"))
        print("business_area:", poi.get("business_area"))
        print("district:", poi.get("district"))
        print("adcode:", poi.get("adcode"))
```

**建议**:
- M4第一步：在生产环境运行上述检查脚本
- 如果生产环境返回完整字段，考虑优化`transit_estimator.py`逻辑
- 如果生产环境同样缺少字段，确认降级逻辑在所有城市下正确

---

### 3. asyncio调用链安全性 ✅

**本地环境**:
- `chat_flow.py`的`run()`方法是同步的（无`async def`）
- `mcp_gateway.py`的`_trip()`方法使用`asyncio.run()`
- 已添加`asyncio.get_running_loop()`检测

**生产环境**:
- `chat_flow.py`的`run()`方法是同步的 ✅
- 调用链：`ChatFlow.run()` -> `ToolExecutor.execute()` -> `MCPToolGateway.invoke()` -> `_trip()`
- 全链路同步，不存在event loop冲突

**验证结果**:
```python
# chat_flow.py line 115
def run(self, req: ChatRequest) -> ChatResponse:
    # 同步方法，无async关键字
```

**结论**: ✅ asyncio安全检测在生产环境同样有效
- 生产环境调用链是同步的
- `asyncio.run()`在`_trip()`中安全使用
- `asyncio.get_running_loop()`检测作为防御性编程保留

---

### 4. 其他环境差异

#### 4.1 高德MCP启动方式

**本地环境**:
- 通过`AmapMCPClient`启动子进程
- 命令：`npx -y @amap/amap-maps-mcp-server`
- 环境变量：`AMAP_MAPS_API_KEY`

**生产环境**:
- 启动方式相同（通过`AmapMCPClient`）
- 需要确认：
  - `npx`命令是否可用
  - `AMAP_API_KEY`环境变量是否配置
  - 网络是否允许访问高德API

**建议**: M4第一步确认生产环境MCP启动成功

#### 4.2 LLM超时配置

**本地环境**:
- `LM_STUDIO_TIMEOUT_SEC=60`（默认）
- LLM重写超时：未单独配置

**生产环境**:
- 需要确认超时配置是否合理
- 建议：
  - `LM_STUDIO_TIMEOUT_SEC=30`（生产环境降低超时）
  - 添加`PLAN_TRIP_LLM_TIMEOUT_SEC=20`（行程规划专用超时）

#### 4.3 Mock数据降级

**本地环境**:
- 当高德MCP不可用时，降级到`mock_plan_trip()`
- Mock数据仅用于开发测试

**生产环境**:
- 需要确认：是否允许降级到Mock数据？
- 建议：生产环境禁用Mock降级，直接返回错误

---

## M4第一步：环境对齐检查清单

在M4开始编码前，必须完成以下检查：

### 检查1: 确认生产环境LLM配置

```bash
# 检查环境变量
echo $AGENT_BACKEND  # 应该是 lmstudio 或 coze
echo $LM_STUDIO_MODEL  # 如果是lmstudio，应该是 qwen2.5-7b-instruct-mlx
echo $COZE_BOT_ID  # 如果是coze，检查是否配置
```

**通过标准**: 
- 如果`AGENT_BACKEND=lmstudio`且`LM_STUDIO_MODEL=qwen2.5-7b-instruct-mlx`，无需重新验证
- 如果使用Coze，需要重新运行M3端到端测试验证输出质量

### 检查2: 验证高德MCP POI字段完整性

```python
# 在生产环境运行
python -c "
import sys
sys.path.insert(0, 'agent_service')
from infra.tool_clients.amap_mcp_client import AmapMCPClient

client = AmapMCPClient()
result = client.find_nearby(keyword='星巴克', city='上海')

if result.ok and result.raw:
    pois = result.raw.get('pois', [])
    if pois:
        poi = pois[0]
        print('POI字段:', list(poi.keys()))
        print('location:', poi.get('location'))
        print('business_area:', poi.get('business_area'))
        print('district:', poi.get('district'))
        print('adcode:', poi.get('adcode'))
"
```

**通过标准**:
- 如果返回完整字段，记录在案，考虑优化降级逻辑
- 如果缺少字段，确认与本地环境一致，降级逻辑有效

### 检查3: 确认高德MCP启动成功

```bash
# 检查npx是否可用
which npx

# 检查环境变量
echo $AMAP_API_KEY

# 测试MCP启动
python -c "
import sys
sys.path.insert(0, 'agent_service')
from infra.tool_clients.amap_mcp_client import AmapMCPClient

client = AmapMCPClient()
try:
    result = client.find_nearby(keyword='咖啡', city='北京')
    print('MCP启动成功:', result.ok)
except Exception as e:
    print('MCP启动失败:', e)
"
```

**通过标准**: MCP启动成功且能正常返回数据

### 检查4: 运行M3快速验证测试

```bash
# 在生产环境运行M3快速验证
python tests/integration/test_m5_4_plan_trip_m3_quick.py
```

**通过标准**: 
- 驾车+城市+旅游信号词修复：3/3通过
- 端到端快速验证：5/5通过
- 交通时间错误：0/5

---

## 风险评估

| 风险项 | 严重程度 | 概率 | 缓解措施 |
|--------|----------|------|----------|
| 生产环境使用不同LLM模型 | 高 | 中 | M4第一步确认AGENT_BACKEND配置 |
| 高德MCP POI字段差异 | 中 | 中 | 运行字段检查脚本 |
| 高德MCP启动失败 | 高 | 低 | 确认npx和环境变量 |
| Mock数据在生产环境误触发 | 中 | 低 | 考虑禁用生产环境Mock降级 |
| asyncio event loop冲突 | 低 | 低 | 已添加检测逻辑 |

---

## M4实施建议

### 阶段1: 环境对齐（1-2小时）

1. 运行上述4个检查清单
2. 记录生产环境配置差异
3. 如果发现差异，评估是否需要调整代码

### 阶段2: 生产环境集成（2-3小时）

1. 在`chat_flow.py`中集成`trip_router`
2. 更新`ToolExecutor`支持`plan_trip`工具
3. 添加生产环境配置（超时、降级策略）

### 阶段3: 生产环境测试（1-2小时）

1. 运行M3完整测试套件（15正例+8负例+10端到端）
2. 验证输出质量与本地一致
3. 验证交通时间降级逻辑正确

### 阶段4: 性能优化（可选）

1. 如果生产环境POI返回完整字段，优化交通时间计算
2. 调整LLM超时配置
3. 添加监控和日志

---

## 总结

**环境一致性评估**:
- ✅ LLM模型一致（qwen2.5-7b-instruct-mlx）
- ⚠️ 高德MCP POI字段需要验证
- ✅ asyncio调用链安全
- ⚠️ 其他配置需要确认

**M4第一步**:
不是写代码，是运行4个环境对齐检查，确认生产环境配置与本地一致。

**预期结果**:
如果环境对齐检查全部通过，M3的100%测试覆盖在生产环境同样有效。

---

**创建时间**: 2026-03-09  
**状态**: 待M4环境对齐检查
