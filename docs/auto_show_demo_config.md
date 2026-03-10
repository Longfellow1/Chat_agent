# 车展演示环境配置指南

## 场景说明

车展演示环境特点：
- 请求量不大（演示场景）
- 需要高可用性（不能在演示时挂掉）
- API额度有限（需要多重冗余避免耗尽）
- 响应速度要求高（演示体验）

## 多重冗余策略

### Web Search 降级链

```
baidu_ai_search (优先级1, AI搜索, 直通)
    ↓ 失败/额度用完
baidu_search (优先级2, 传统搜索, 需处理)
    ↓ 失败/额度用完
tavily (优先级3, 传统搜索, 需处理)
    ↓ 失败
坦诚报错（不使用 Mock）
```

### 设计理念

1. **优先使用 AI 搜索**: Baidu AI Search 返回对话式文本，直接可用，体验最好
2. **百度备份**: Baidu Search 作为第二选择，保持百度生态
3. **Tavily 兜底**: 最后使用 Tavily，失败则坦诚报错
4. **分散 API 额度**: 多个 Provider 分担请求，避免单一 API 额度耗尽
5. **坦诚报错**: 所有 Provider 失败时，向用户说明情况，不返回虚假数据

## 环境变量配置

### 推荐配置（车展演示）

```bash
# ===== Web Search Providers =====

# Baidu AI Search (优先级1 - AI搜索)
export BAIDU_AI_SEARCH_ENABLED=true
export BAIDU_AI_SEARCH_API_KEY=your_baidu_ai_key
export BAIDU_AI_SEARCH_TIMEOUT=2.5  # 车展演示：压缩超时避免等待过长

# Baidu Search (优先级2 - 传统搜索)
export BAIDU_SEARCH_ENABLED=true
export BAIDU_SEARCH_API_KEY=your_baidu_search_key
export BAIDU_SEARCH_TIMEOUT=3.0

# Tavily (优先级3 - 传统搜索，最后兜底)
export TAVILY_ENABLED=true
export TAVILY_API_KEY=your_tavily_key
export TAVILY_TIMEOUT=3.0

# ===== Location Providers =====

# Amap MCP (优先级1)
export AMAP_MCP_ENABLED=true
export AMAP_API_KEY=your_amap_key
export AMAP_MCP_TIMEOUT=3.0

# Amap Direct (优先级2 - 备份)
export AMAP_DIRECT_ENABLED=true
export AMAP_DIRECT_TIMEOUT=2.0

# Web Search Fallback (优先级3 - 最后备选)
export WEB_FALLBACK_ENABLED=true

# ===== 通用配置 =====
export TOOL_SEARCH_MAX_RESULTS=3
export TOOL_SEARCH_SNIPPET_CHARS=80
export ENABLE_NETWORK_FALLBACK=true
```

### 保守配置（API 额度紧张时）

如果某个 API 额度快用完，可以临时禁用：

```bash
# 禁用 Baidu AI Search，优先使用 Baidu Search
export BAIDU_AI_SEARCH_ENABLED=false
export BAIDU_SEARCH_ENABLED=true

# 或者禁用 Baidu Search，只用 AI 和 Tavily
export BAIDU_SEARCH_ENABLED=false
export BAIDU_AI_SEARCH_ENABLED=true
export TAVILY_ENABLED=true
```

## 运行时监控

### 查看 API 使用情况

```python
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3

gateway = MCPToolGatewayV3()

# 查看各 Provider 的调用统计
metrics = gateway.get_provider_metrics("web_search")

for provider, stats in metrics.items():
    print(f"\n{provider}:")
    print(f"  总调用: {stats['total_calls']}")
    print(f"  成功: {stats['success_calls']}")
    print(f"  失败: {stats['failed_calls']}")
    print(f"  降级次数: {stats['fallback_count']}")
    
    # 计算使用率
    if stats['total_calls'] > 0:
        usage_rate = stats['success_calls'] / stats['total_calls']
        print(f"  使用率: {usage_rate:.2%}")
```

### 动态调整策略

演示过程中如果发现某个 API 快用完：

```python
# 临时禁用某个 Provider
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=False)

# 调整优先级（通过超时控制）
gateway.update_provider_config("web_search", "tavily", timeout=1.0)  # 快速失败，降级
```

## 降级场景示例

### 场景1: Baidu AI 额度用完

```
用户查询: "特斯拉 Model 3 价格"
↓
baidu_ai_search → quota_exceeded (额度用完)
↓
baidu_search → 成功返回原始结果
↓
结果: 
  - provider_name: baidu_search
  - result_type: raw (经过 search_result_processor 处理)
  - fallback_chain: ["baidu_ai_search:quota_exceeded"]
```

### 场景2: 多个 API 都接近限额

```
用户查询: "比亚迪汉 EV 续航"
↓
baidu_ai_search → rate_limit (限流)
↓
baidu_search → rate_limit (限流)
↓
tavily → 成功返回
↓
结果:
  - provider_name: tavily
  - result_type: raw
  - fallback_chain: ["baidu_ai_search:rate_limit", "baidu_search:rate_limit"]
```

### 场景3: 所有 API 都失败

```
用户查询: "蔚来 ET7 配置"
↓
baidu_ai_search → 失败
↓
baidu_search → 失败
↓
tavily → 失败
↓
坦诚报错
↓
结果:
  - ok: False
  - error: "All providers failed"
  - text: "抱歉，当前搜索服务暂时不可用，请稍后再试"
  - fallback_chain: ["baidu_ai_search:error", "baidu_search:error", "tavily:error"]
```

## Result Type 处理差异

### AI 搜索（SUMMARIZED）

```python
# Baidu AI Search 返回
result_type = ResultType.SUMMARIZED

# 直接使用，不经过 search_result_processor
text = "特斯拉 Model 3 是一款纯电动中型轿车，起售价约 26 万元..."
# 直通路径，保持 AI 生成的对话式文本
```

### 传统搜索（RAW）

```python
# Tavily / Baidu Search 返回
result_type = ResultType.RAW

# 经过 search_result_processor 处理
results = [
    {"title": "特斯拉官网", "url": "...", "snippet": "..."},
    {"title": "汽车之家", "url": "...", "snippet": "..."},
]
# 处理：相关性过滤 + 可信度评分 + 格式化
```

## 演示前检查清单

### 1. API Key 配置

```bash
# 检查所有 API Key 是否配置
echo "Baidu AI: ${BAIDU_AI_SEARCH_API_KEY:0:10}..."
echo "Tavily: ${TAVILY_API_KEY:0:10}..."
echo "Baidu Search: ${BAIDU_SEARCH_API_KEY:0:10}..."
echo "Amap: ${AMAP_API_KEY:0:10}..."
```

### 2. Provider 健康检查

```python
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3

gateway = MCPToolGatewayV3()

# 测试每个 Provider
test_queries = [
    ("web_search", {"query": "测试"}),
    ("find_nearby", {"keyword": "咖啡厅", "city": "上海"}),
]

for tool, args in test_queries:
    result = gateway.invoke(tool, args)
    print(f"{tool}: {'✅ OK' if result.ok else '❌ FAIL'}")
    if result.raw:
        print(f"  Provider: {result.raw.get('provider_name')}")
```

### 3. 额度检查

演示前确认各 API 剩余额度：
- Baidu AI Search: 检查控制台
- Tavily: 检查 Dashboard
- Baidu Search: 检查控制台
- Amap: 检查控制台

### 4. 降级测试

```python
# 模拟主 Provider 失败
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=False)

result = gateway.invoke("web_search", {"query": "测试降级"})
print(f"降级到: {result.raw.get('provider_name')}")
print(f"降级链: {result.raw.get('fallback_chain')}")

# 恢复
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=True)
```

## 演示中应急方案

### 方案1: 某个 API 突然失败

```python
# 立即禁用失败的 Provider
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=False)
```

### 方案2: 所有 API 都接近限额

```python
# 调整超时，快速降级到 Mock
gateway.update_provider_config("web_search", "baidu_ai_search", timeout=0.5)
gateway.update_provider_config("web_search", "tavily", timeout=0.5)
gateway.update_provider_config("web_search", "baidu_search", timeout=0.5)
```

### 方案3: 响应太慢

```python
# 减少超时，提升响应速度
gateway.update_provider_config("web_search", "baidu_ai_search", timeout=2.0)
gateway.update_provider_config("web_search", "tavily", timeout=1.5)
```

## 性能优化建议

### 1. 预热

演示前执行几次查询，让系统预热：

```python
warmup_queries = [
    "特斯拉 Model 3",
    "上海 咖啡厅",
    "比亚迪汉 EV",
]

for query in warmup_queries:
    gateway.invoke("web_search", {"query": query})
```

### 2. 缓存（可选）

如果演示内容固定，可以预先缓存结果：

```python
# 预先执行并缓存
demo_queries = {
    "特斯拉价格": gateway.invoke("web_search", {"query": "特斯拉 Model 3 价格"}),
    "上海咖啡": gateway.invoke("find_nearby", {"keyword": "咖啡厅", "city": "上海"}),
}

# 演示时直接使用缓存
result = demo_queries.get(user_query)
```

### 3. 监控面板

演示时开启监控面板，实时查看：

```python
import time
import threading

def monitor_loop():
    while True:
        metrics = gateway.get_provider_metrics("web_search")
        print("\n=== Provider Status ===")
        for provider, stats in metrics.items():
            print(f"{provider}: {stats['success_calls']}/{stats['total_calls']} "
                  f"({stats['success_rate']:.1%})")
        time.sleep(10)

# 后台运行
threading.Thread(target=monitor_loop, daemon=True).start()
```

## 总结

车展演示配置的核心原则：

1. **多重冗余**: 3个搜索 Provider 确保高可用
2. **分散额度**: 避免单一 API 耗尽
3. **快速降级**: 超时设置合理，快速切换
4. **实时监控**: 随时查看使用情况
5. **应急预案**: 准备好临时调整方案
6. **坦诚报错**: 所有 Provider 失败时，向用户说明情况，不返回虚假数据

这套配置可以确保演示过程中即使某个 API 出问题，也能无缝切换到备选方案，保证演示顺利进行。
