# Provider Chain 使用指南

## 快速开始

### 1. 基本使用

```python
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3

# 初始化Gateway（自动加载配置）
gateway = MCPToolGatewayV3()

# 调用工具（自动降级）
result = gateway.invoke(
    "find_nearby",
    {"keyword": "咖啡厅", "city": "上海"}
)

if result.ok:
    print(result.text)
    print(f"Provider: {result.raw['provider_name']}")
    print(f"延迟: {result.raw['provider_latency_ms']}ms")
    
    # 检查是否发生了降级
    if result.raw.get('fallback_chain'):
        print(f"降级链: {result.raw['fallback_chain']}")
```

### 2. 查看Provider指标

```python
# 获取所有Provider的指标
metrics = gateway.get_provider_metrics("find_nearby")

for provider_name, stats in metrics.items():
    print(f"\n{provider_name}:")
    print(f"  总调用: {stats['total_calls']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  平均延迟: {stats['avg_latency_ms']:.2f}ms")
    print(f"  降级次数: {stats['fallback_count']}")
```

### 3. 运行时配置调整

```python
# 禁用某个Provider
gateway.update_provider_config(
    "find_nearby",
    "amap_mcp",
    enabled=False
)

# 调整超时
gateway.update_provider_config(
    "find_nearby",
    "amap_direct",
    timeout=5.0
)

# 启用降级
gateway.update_provider_config(
    "web_search",
    "tavily",
    fallback_on_timeout=True
)
```

## 环境变量配置

### 全局配置

```bash
# 启用/禁用Provider
export AMAP_MCP_ENABLED=true
export AMAP_DIRECT_ENABLED=true
export WEB_FALLBACK_ENABLED=true
export TAVILY_ENABLED=true

# 超时配置
export AMAP_MCP_TIMEOUT=3.0
export AMAP_DIRECT_TIMEOUT=2.0
export TAVILY_TIMEOUT=3.0

# API Keys
export AMAP_API_KEY=your_key
export TAVILY_API_KEY=your_key
```

### Provider特定配置

```bash
# 格式: {PROVIDER_NAME}_{CONFIG_KEY}
export AMAP_MCP_TIMEOUT=5.0
export AMAP_MCP_ENABLED=false
export TAVILY_TIMEOUT=4.0
```

## Provider链配置

### 当前配置

#### find_nearby
1. **amap_mcp** (优先级1)
   - 超时: 3秒
   - 重试: 2次
   - 降级条件: 超时、错误、无结果

2. **amap_direct** (优先级2)
   - 超时: 2秒
   - 重试: 1次
   - 降级条件: 超时、错误、无结果

3. **web_search_fallback** (优先级3)
   - 超时: 3秒
   - 重试: 1次
   - 不降级（最后的真实数据源）

4. **mock** (优先级99)
   - 超时: 0.1秒
   - 不降级（兜底）

#### web_search
1. **tavily** (优先级1)
   - 超时: 3秒
   - 重试: 2次
   - 降级条件: 超时、错误、无结果

2. **mock** (优先级99)
   - 兜底

## 降级场景示例

### 场景1: 主Provider超时

```
用户查询: "上海 咖啡厅"
↓
amap_mcp (3秒超时) → 超时
↓
amap_direct (2秒) → 成功返回
↓
结果: 
  - provider_name: amap_direct
  - fallback_chain: ["amap_mcp:timeout"]
```

### 场景2: 多级降级

```
用户查询: "上海 咖啡厅"
↓
amap_mcp → 无结果
↓
amap_direct → API限流
↓
web_search_fallback → 成功返回
↓
结果:
  - provider_name: web_search_fallback
  - fallback_chain: ["amap_mcp:no_results", "amap_direct:api_limit"]
```

### 场景3: 全部失败

```
用户查询: "上海 咖啡厅"
↓
amap_mcp → 失败
↓
amap_direct → 失败
↓
web_search_fallback → 失败
↓
mock → 返回Mock数据
↓
结果:
  - provider_name: mock
  - fallback_chain: ["amap_mcp:error", "amap_direct:error", "web_search_fallback:error"]
```

## 自定义Provider

### 1. 实现Provider接口

```python
from infra.tool_clients.provider_base import ToolProvider, ProviderConfig, ProviderResult

class MyCustomProvider(ToolProvider):
    """自定义Provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # 初始化客户端
        self.client = MyClient()
    
    def execute(self, **kwargs) -> ProviderResult:
        """执行工具调用."""
        try:
            # 调用外部服务
            data = self.client.call(**kwargs)
            
            return ProviderResult(
                ok=True,
                data=data,
                provider_name=self.config.name,
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=str(e),
            )
    
    def health_check(self) -> bool:
        """健康检查."""
        try:
            return self.client.ping()
        except:
            return False
```

### 2. 注册Provider

```python
from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.provider_chain import ProviderChainManager

manager = ProviderChainManager()

# 注册
manager.register_provider("my_custom", MyCustomProvider)

# 配置链
config = [
    ProviderConfig(
        name="my_custom",
        priority=1,
        timeout=3.0,
        fallback_on_timeout=True,
        fallback_on_error=True,
    ),
    ProviderConfig(
        name="mock",
        priority=99,
        timeout=0.1,
    ),
]
manager.configure_chain("my_tool", config)

# 使用
result = manager.execute("my_tool", keyword="test")
```

## 监控和调试

### 1. 查看降级链

```python
result = gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"})

if result.raw.get('fallback_chain'):
    print("发生了降级:")
    for step in result.raw['fallback_chain']:
        print(f"  - {step}")
```

### 2. 监控Provider健康

```python
metrics = gateway.get_provider_metrics("find_nearby")

for provider, stats in metrics.items():
    if stats['success_rate'] < 0.8:
        print(f"警告: {provider} 成功率过低 ({stats['success_rate']:.2%})")
    
    if stats['avg_latency_ms'] > 2000:
        print(f"警告: {provider} 延迟过高 ({stats['avg_latency_ms']:.0f}ms)")
```

### 3. 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

result = gateway.invoke("find_nearby", {"keyword": "咖啡厅"})

logger.info(
    f"Tool call: provider={result.raw['provider_name']}, "
    f"latency={result.raw['provider_latency_ms']:.2f}ms, "
    f"fallback={result.raw.get('fallback_chain')}"
)
```

## 最佳实践

### 1. Provider优先级设置

- **优先级1-10**: 主要数据源（官方API、MCP服务器）
- **优先级11-50**: 备选数据源（其他API、爬虫）
- **优先级51-90**: 降级方案（Web搜索、缓存）
- **优先级91-99**: 兜底方案（Mock、默认值）

### 2. 超时配置

- **快速API**: 1-2秒
- **标准API**: 2-3秒
- **慢速API**: 3-5秒
- **Web搜索**: 3-5秒
- **Mock**: 0.1秒

### 3. 降级策略

- **主Provider**: 启用所有降级（timeout + error）
- **备选Provider**: 启用错误降级，谨慎超时降级
- **最后真实源**: 不降级（返回错误给用户）
- **Mock**: 永不降级（兜底）

### 4. 错误码配置

```python
ProviderConfig(
    name="amap_mcp",
    fallback_error_codes=[
        "no_results",      # 无结果
        "api_limit",       # API限流
        "rate_limit",      # 速率限制
        "service_unavailable",  # 服务不可用
    ]
)
```

### 5. 健康检查

- 设置合理的检查间隔（30-120秒）
- 使用轻量级检查（避免实际调用）
- 失败后标记为DEGRADED而非UNAVAILABLE

## 故障排查

### Provider不可用

```python
# 检查Provider状态
metrics = gateway.get_provider_metrics("find_nearby")
if "amap_mcp" not in metrics or metrics["amap_mcp"]["total_calls"] == 0:
    print("amap_mcp未被调用，可能被禁用或不可用")

# 检查配置
gateway.update_provider_config("find_nearby", "amap_mcp", enabled=True)
```

### 频繁降级

```python
# 检查降级次数
metrics = gateway.get_provider_metrics("find_nearby")
for provider, stats in metrics.items():
    fallback_rate = stats['fallback_count'] / max(stats['total_calls'], 1)
    if fallback_rate > 0.5:
        print(f"{provider} 降级率过高: {fallback_rate:.2%}")
        # 考虑调整超时或禁用该Provider
```

### 性能问题

```python
# 检查延迟
metrics = gateway.get_provider_metrics("find_nearby")
for provider, stats in metrics.items():
    if stats['avg_latency_ms'] > 3000:
        print(f"{provider} 延迟过高，考虑降低优先级或调整超时")
```

## 总结

Provider Chain架构提供了：

1. ✅ **自动降级**: 主Provider失败自动切换
2. ✅ **灵活配置**: 环境变量 + 运行时调整
3. ✅ **可观测性**: 完整的指标和降级链追踪
4. ✅ **易扩展**: 实现接口即可添加新Provider
5. ✅ **高可用**: 多级降级保证服务可用性
