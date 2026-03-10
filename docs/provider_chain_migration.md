# Provider Chain 迁移指南

## 概述

本指南帮助你从现有的 `MCPToolGateway` / `MCPToolGatewayV2` 迁移到新的 `MCPToolGatewayV3`（基于Provider Chain）。

## 为什么要迁移？

### 现有问题
- ❌ 主线路挂了没有备选方案
- ❌ 每个信源需要重复实现客户端
- ❌ 配置分散，难以管理
- ❌ 切换信源需要修改代码

### 迁移后的优势
- ✅ 自动降级到备选Provider
- ✅ 统一的Provider接口
- ✅ 集中配置管理
- ✅ 运行时动态切换
- ✅ 完整的监控指标

## 迁移步骤

### Phase 1: 评估现状

#### 1.1 识别现有工具调用

```python
# 现有代码
from infra.tool_clients.mcp_gateway import MCPToolGateway

gateway = MCPToolGateway()
result = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})
```

#### 1.2 识别依赖的外部服务

- Amap API (MCP + Direct)
- Tavily API
- QWeather API
- Alpha Vantage API
- Mock services

### Phase 2: 无缝切换

#### 2.1 替换Gateway实例

```python
# 旧代码
from infra.tool_clients.mcp_gateway import MCPToolGateway
gateway = MCPToolGateway()

# 新代码（向后兼容）
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3
gateway = MCPToolGatewayV3()

# 调用方式完全相同
result = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})
```

#### 2.2 验证功能

```bash
# 运行现有测试
pytest tests/unit/test_location_intent.py
pytest tests/integration/test_location_end_to_end.py

# 运行新的Provider测试
pytest tests/unit/test_provider_chain.py
```

### Phase 3: 利用新特性

#### 3.1 查看降级链

```python
result = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})

# 新增字段
if result.raw:
    print(f"Provider: {result.raw.get('provider_name')}")
    print(f"延迟: {result.raw.get('provider_latency_ms')}ms")
    
    if result.raw.get('fallback_chain'):
        print(f"降级链: {result.raw['fallback_chain']}")
```

#### 3.2 监控Provider健康

```python
# 新增方法
metrics = gateway.get_provider_metrics("find_nearby")

for provider, stats in metrics.items():
    print(f"{provider}: 成功率 {stats['success_rate']:.2%}, "
          f"平均延迟 {stats['avg_latency_ms']:.0f}ms")
```

#### 3.3 动态配置调整

```python
# 新增方法
gateway.update_provider_config(
    "find_nearby",
    "amap_mcp",
    enabled=False  # 临时禁用
)
```

### Phase 4: 配置优化

#### 4.1 环境变量配置

```bash
# .env 文件
# Provider启用/禁用
AMAP_MCP_ENABLED=true
AMAP_DIRECT_ENABLED=true
WEB_FALLBACK_ENABLED=true

# 超时配置
AMAP_MCP_TIMEOUT=3.0
AMAP_DIRECT_TIMEOUT=2.0
TAVILY_TIMEOUT=3.0

# API Keys（保持不变）
AMAP_API_KEY=your_key
TAVILY_API_KEY=your_key
```

#### 4.2 自定义Provider链

```python
from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3

gateway = MCPToolGatewayV3()

# 自定义配置
custom_config = [
    ProviderConfig(
        name="amap_mcp",
        priority=1,
        timeout=5.0,  # 增加超时
        fallback_on_timeout=True,
    ),
    ProviderConfig(
        name="amap_direct",
        priority=2,
        timeout=3.0,
        enabled=False,  # 禁用
    ),
]

gateway.chain_manager.configure_chain("find_nearby", custom_config)
```

## 兼容性说明

### 完全兼容

以下代码无需修改：

```python
# ✅ 基本调用
result = gateway.invoke("find_nearby", {"keyword": "咖啡厅"})

# ✅ 结果检查
if result.ok:
    print(result.text)

# ✅ 错误处理
if not result.ok:
    print(result.error)

# ✅ 原始数据访问
if result.raw:
    pois = result.raw.get("pois", [])
```

### 新增字段

以下字段是新增的，不影响现有代码：

```python
# 新增字段（可选使用）
result.raw["provider_name"]        # Provider名称
result.raw["provider_latency_ms"]  # Provider延迟
result.raw["fallback_chain"]       # 降级链（如果发生降级）
```

### 行为变化

#### 1. 降级行为

**旧版本**:
```python
# Amap失败 → 直接返回错误或降级到Mock
result = gateway.invoke("find_nearby", {"keyword": "咖啡厅"})
# 可能直接失败
```

**新版本**:
```python
# Amap MCP失败 → Amap Direct → Web Search → Mock
result = gateway.invoke("find_nearby", {"keyword": "咖啡厅"})
# 更高的成功率
```

#### 2. 错误信息

**旧版本**:
```python
result.error = "amap_fail:timeout"
```

**新版本**:
```python
result.error = "amap_mcp_error:timeout"
result.raw["fallback_chain"] = ["amap_mcp:timeout"]
```

## 迁移检查清单

### 代码层面

- [ ] 替换 `MCPToolGateway` 为 `MCPToolGatewayV3`
- [ ] 运行所有现有测试
- [ ] 验证关键功能正常
- [ ] 添加降级链日志（可选）
- [ ] 添加Provider监控（可选）

### 配置层面

- [ ] 检查环境变量配置
- [ ] 设置Provider超时
- [ ] 配置降级策略
- [ ] 测试各Provider可用性

### 测试层面

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试关键场景
- [ ] 测试降级场景
- [ ] 测试Provider切换

### 监控层面

- [ ] 添加Provider指标监控
- [ ] 添加降级告警
- [ ] 添加性能监控
- [ ] 添加错误率监控

## 回滚方案

如果迁移后出现问题，可以快速回滚：

```python
# 方案1: 代码回滚
from infra.tool_clients.mcp_gateway import MCPToolGateway
gateway = MCPToolGateway()

# 方案2: 禁用Provider Chain
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3
gateway = MCPToolGatewayV3()

# 禁用所有备选Provider，只保留主Provider
gateway.update_provider_config("find_nearby", "amap_direct", enabled=False)
gateway.update_provider_config("find_nearby", "web_search_fallback", enabled=False)
```

## 常见问题

### Q1: 迁移后性能会变差吗？

A: 不会。Provider Chain只在主Provider失败时才会尝试备选，成功路径的性能与旧版本相同。

### Q2: 如何禁用自动降级？

A: 通过配置禁用降级：

```python
gateway.update_provider_config(
    "find_nearby",
    "amap_mcp",
    fallback_on_error=False,
    fallback_on_timeout=False
)
```

### Q3: 如何只使用一个Provider？

A: 禁用其他Provider：

```python
gateway.update_provider_config("find_nearby", "amap_direct", enabled=False)
gateway.update_provider_config("find_nearby", "web_search_fallback", enabled=False)
gateway.update_provider_config("find_nearby", "mock", enabled=False)
```

### Q4: 降级会增加延迟吗？

A: 只有在主Provider失败时才会增加延迟。可以通过调整超时来控制：

```python
# 减少超时以快速降级
gateway.update_provider_config("find_nearby", "amap_mcp", timeout=1.0)
```

### Q5: 如何添加自定义Provider？

A: 参考 [Provider Chain 使用指南](./provider_chain_usage.md#自定义provider)

## 迁移时间表

### 建议的迁移节奏

**Week 1: 准备**
- 阅读文档
- 评估现状
- 制定计划

**Week 2: 开发环境迁移**
- 替换Gateway
- 运行测试
- 验证功能

**Week 3: 测试环境迁移**
- 部署到测试环境
- 监控指标
- 修复问题

**Week 4: 生产环境迁移**
- 灰度发布
- 监控告警
- 全量发布

## 支持

如有问题，请：

1. 查看 [Provider Chain 使用指南](./provider_chain_usage.md)
2. 查看 [架构设计文档](../spec/unified_tool_management_architecture.md)
3. 运行测试: `pytest tests/unit/test_provider_chain.py -v`
4. 提交Issue

## 总结

迁移到Provider Chain架构可以：

1. ✅ 提高服务可用性（自动降级）
2. ✅ 简化代码维护（统一接口）
3. ✅ 增强可观测性（指标监控）
4. ✅ 提升灵活性（动态配置）

迁移过程向后兼容，风险可控，建议尽快迁移。
