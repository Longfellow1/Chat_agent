# 车展演示前检查清单

## 演示前1天

### 1. 环境配置检查

- [ ] 所有 API Key 已配置并验证
  ```bash
  echo "Baidu AI: ${BAIDU_AI_SEARCH_API_KEY:0:10}..."
  echo "Baidu Search: ${BAIDU_SEARCH_API_KEY:0:10}..."
  echo "Tavily: ${TAVILY_API_KEY:0:10}..."
  echo "Amap: ${AMAP_API_KEY:0:10}..."
  ```

- [ ] 超时配置已优化
  ```bash
  # 确认配置
  grep "BAIDU_AI_SEARCH_TIMEOUT" .env
  # 应该是 2.5 而不是 4.0
  ```

- [ ] Provider 优先级正确
  ```
  1. baidu_ai_search (2.5s)
  2. baidu_search (3s)
  3. tavily (3s)
  ```

### 2. 额度检查

- [ ] Baidu AI Search 额度充足（建议 > 50 次）
- [ ] Baidu Search 额度充足（建议 > 200 次）
- [ ] Tavily 额度充足（建议 > 100 次）
- [ ] Amap 额度充足（建议 > 200 次）

### 3. 预热执行

- [ ] 运行预热脚本
  ```bash
  cd agent_service
  python docs/auto_show_warmup_queries.py
  ```

- [ ] 预热结果：20/20 成功
- [ ] 缓存已建立
- [ ] 无额度告警

### 4. 降级链测试

- [ ] 测试1: 正常流程（baidu_ai_search）
- [ ] 测试2: 一级降级（baidu_search）
- [ ] 测试3: 二级降级（tavily）
- [ ] 测试4: 全部失败（坦诚报错）

### 5. 性能测试

- [ ] 平均响应时间 < 3秒
- [ ] 最大响应时间 < 5秒
- [ ] 缓存命中率 > 0%

### 6. 监控准备

- [ ] 额度监控脚本准备就绪
- [ ] 缓存状态查看脚本准备就绪
- [ ] 应急方案文档已打印/保存

## 演示当天早上

### 1. 再次预热

- [ ] 运行预热脚本（刷新缓存）
- [ ] 检查额度状态
  ```python
  from infra.tool_clients.quota_monitor import QuotaMonitor
  monitor = QuotaMonitor()
  print(monitor.get_status_report())
  ```

### 2. 网络检查

- [ ] 测试网络连接
- [ ] 测试各 API 可达性
- [ ] 确认现场 WiFi 稳定

### 3. 快速验证

- [ ] 执行3-5个测试查询
- [ ] 确认响应正常
- [ ] 确认降级链正常

### 4. 准备应急工具

- [ ] 笔记本电脑充满电
- [ ] 手机热点备用
- [ ] 应急命令清单打印

## 演示过程中

### 实时监控

每30分钟检查一次：

```python
# 快速检查脚本
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3
from infra.tool_clients.quota_monitor import QuotaMonitor

gateway = MCPToolGatewayV3()
monitor = QuotaMonitor()

# 查看 Provider 指标
metrics = gateway.get_provider_metrics("web_search")
for provider, stats in metrics.items():
    print(f"{provider}: {stats['success_calls']}/{stats['total_calls']} ({stats['success_rate']:.1%})")

# 查看额度状态
print(monitor.get_status_report())

# 检查告警
warnings = monitor.check_warnings()
if warnings:
    print("⚠️  告警:", warnings)
```

### 应急响应

#### 场景1: Baidu AI Search 额度告警

```python
# 临时禁用 Baidu AI Search
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=False)
print("✅ 已切换到 Baidu Search")
```

#### 场景2: 响应太慢

```python
# 减少超时，快速降级
gateway.update_provider_config("web_search", "baidu_ai_search", timeout=1.5)
gateway.update_provider_config("web_search", "baidu_search", timeout=2.0)
print("✅ 已优化超时配置")
```

#### 场景3: 某个 Provider 持续失败

```python
# 禁用失败的 Provider
gateway.update_provider_config("web_search", "baidu_search", enabled=False)
print("✅ 已禁用故障 Provider")
```

#### 场景4: 网络问题

```bash
# 切换到手机热点
# 重新测试连接
curl -I https://api.baidu.com
curl -I https://api.tavily.com
```

## 演示后

### 1. 数据收集

- [ ] 导出 Provider 指标
- [ ] 导出额度使用情况
- [ ] 导出缓存命中率
- [ ] 记录异常事件

### 2. 总结报告

```python
# 生成总结报告
from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3
from infra.tool_clients.result_cache import cache
from infra.tool_clients.quota_monitor import QuotaMonitor

gateway = MCPToolGatewayV3()
monitor = QuotaMonitor()

print("=== 演示总结报告 ===\n")

# Provider 使用情况
print("Provider 使用情况:")
metrics = gateway.get_provider_metrics("web_search")
for provider, stats in metrics.items():
    print(f"  {provider}:")
    print(f"    总调用: {stats['total_calls']}")
    print(f"    成功率: {stats['success_rate']:.1%}")
    print(f"    平均延迟: {stats['avg_latency_ms']:.0f}ms")
    print(f"    降级次数: {stats['fallback_count']}")

# 缓存效果
print(f"\n{cache.get_status_report()}")

# 额度消耗
print(f"\n{monitor.get_status_report()}")
```

### 3. 问题记录

- [ ] 记录所有异常情况
- [ ] 记录应急响应措施
- [ ] 记录用户反馈
- [ ] 提出改进建议

## 应急联系方式

### 技术支持
- 后端负责人: [姓名] [电话]
- 运维负责人: [姓名] [电话]
- API 供应商客服: [电话]

### 应急命令速查

```bash
# 查看 Provider 状态
python -c "from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3; g=MCPToolGatewayV3(); print(g.get_provider_metrics('web_search'))"

# 查看额度状态
python -c "from infra.tool_clients.quota_monitor import QuotaMonitor; m=QuotaMonitor(); print(m.get_status_report())"

# 禁用 Provider
python -c "from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3; g=MCPToolGatewayV3(); g.update_provider_config('web_search', 'baidu_ai_search', enabled=False)"

# 清除缓存
python -c "from infra.tool_clients.result_cache import cache; cache.clear(); print('Cache cleared')"

# 重新预热
python docs/auto_show_warmup_queries.py
```

## 成功标准

### 必须达成
- [ ] 演示过程无中断
- [ ] 响应时间 < 5秒
- [ ] 无假数据展示
- [ ] 降级链正常工作

### 期望达成
- [ ] 平均响应时间 < 3秒
- [ ] 缓存命中率 > 30%
- [ ] 无需手动干预
- [ ] 用户体验良好

### 加分项
- [ ] 所有查询都命中主 Provider
- [ ] 无额度告警
- [ ] 无降级发生
- [ ] 响应时间 < 2秒
