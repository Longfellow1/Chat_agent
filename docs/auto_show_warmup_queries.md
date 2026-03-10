# 车展演示预热查询词表

## 高频查询（预期被问到的问题）

### 电动车价格类（5条）
1. "特斯拉 Model 3 价格"
2. "比亚迪汉 EV 多少钱"
3. "蔚来 ET7 售价"
4. "小鹏 P7 价格"
5. "理想 L9 多少钱"

### 续航里程类（5条）
6. "特斯拉 Model Y 续航"
7. "比亚迪海豹续航多少公里"
8. "蔚来 ES6 续航"
9. "小鹏 G9 续航"
10. "极氪 001 续航"

### 配置参数类（5条）
11. "特斯拉 Model S 配置"
12. "比亚迪唐 EV 参数"
13. "蔚来 ET5 配置"
14. "小鹏 P5 参数"
15. "理想 ONE 配置"

### 充电相关类（3条）
16. "特斯拉充电桩位置"
17. "电动车充电时间"
18. "快充和慢充区别"

### 对比类（2条）
19. "特斯拉和比亚迪哪个好"
20. "蔚来和小鹏对比"

## 预热脚本

```python
"""Auto show warmup script."""

from infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3
from infra.tool_clients.result_cache import ResultCache
from infra.tool_clients.quota_monitor import QuotaMonitor

# 预热查询列表
WARMUP_QUERIES = [
    # 价格类
    "特斯拉 Model 3 价格",
    "比亚迪汉 EV 多少钱",
    "蔚来 ET7 售价",
    "小鹏 P7 价格",
    "理想 L9 多少钱",
    
    # 续航类
    "特斯拉 Model Y 续航",
    "比亚迪海豹续航多少公里",
    "蔚来 ES6 续航",
    "小鹏 G9 续航",
    "极氪 001 续航",
    
    # 配置类
    "特斯拉 Model S 配置",
    "比亚迪唐 EV 参数",
    "蔚来 ET5 配置",
    "小鹏 P5 参数",
    "理想 ONE 配置",
    
    # 充电类
    "特斯拉充电桩位置",
    "电动车充电时间",
    "快充和慢充区别",
    
    # 对比类
    "特斯拉和比亚迪哪个好",
    "蔚来和小鹏对比",
]


def warmup():
    """Execute warmup queries."""
    gateway = MCPToolGatewayV3()
    cache = ResultCache(default_ttl=3600)  # 1 hour cache
    monitor = QuotaMonitor()
    
    print("=== 开始预热 ===\n")
    
    success_count = 0
    failed_queries = []
    
    for i, query in enumerate(WARMUP_QUERIES, 1):
        print(f"[{i}/{len(WARMUP_QUERIES)}] {query}...", end=" ")
        
        try:
            result = gateway.invoke("web_search", {"query": query})
            
            if result.ok:
                # Cache result
                cache.set("web_search", result, query=query)
                
                # Record quota usage
                if result.raw:
                    provider = result.raw.get("provider_name")
                    if provider:
                        monitor.record_usage(provider)
                
                print(f"✅ ({result.raw.get('provider_name', 'unknown')})")
                success_count += 1
            else:
                print(f"❌ {result.error}")
                failed_queries.append((query, result.error))
        
        except Exception as e:
            print(f"❌ Exception: {e}")
            failed_queries.append((query, str(e)))
    
    # Print summary
    print(f"\n=== 预热完成 ===")
    print(f"成功: {success_count}/{len(WARMUP_QUERIES)}")
    print(f"失败: {len(failed_queries)}")
    
    if failed_queries:
        print("\n失败查询:")
        for query, error in failed_queries:
            print(f"  - {query}: {error}")
    
    # Print cache stats
    print(f"\n{cache.get_status_report()}")
    
    # Print quota status
    print(f"\n{monitor.get_status_report()}")
    
    # Check warnings
    warnings = monitor.check_warnings()
    if warnings:
        print("\n⚠️  额度告警:")
        for warning in warnings:
            print(f"  {warning}")
    
    return success_count == len(WARMUP_QUERIES)


if __name__ == "__main__":
    success = warmup()
    exit(0 if success else 1)
```

## 使用方法

### 演示前1天

```bash
# 运行预热脚本
cd agent_service
python -c "from docs.auto_show_warmup_queries import warmup; warmup()"
```

### 演示当天早上

```bash
# 再次预热，确保缓存有效
python -c "from docs.auto_show_warmup_queries import warmup; warmup()"

# 检查额度状态
python -c "
from infra.tool_clients.quota_monitor import QuotaMonitor
monitor = QuotaMonitor()
print(monitor.get_status_report())
"
```

## 预期结果

### 正常情况
- 20条查询全部成功
- 缓存命中率 0%（首次预热）
- 各 Provider 额度消耗均匀
- 无告警

### 异常情况处理

#### 某个 Provider 失败
- 检查降级链是否正常工作
- 确认备选 Provider 可用
- 必要时禁用失败的 Provider

#### 额度告警
- 如果 Baidu AI Search < 20 次，考虑禁用或调整优先级
- 如果多个 Provider 都告警，准备应急方案

#### 响应太慢
- 检查网络环境
- 考虑减少超时时间
- 准备离线缓存方案

## 缓存策略

### 缓存时长
- 价格类: 1小时（价格变化不频繁）
- 续航类: 2小时（参数固定）
- 配置类: 2小时（参数固定）
- 充电类: 30分钟（位置可能变化）
- 对比类: 1小时（主观内容）

### 缓存更新
演示过程中如果发现缓存内容过时：

```python
from infra.tool_clients.result_cache import cache

# 清除特定查询的缓存
cache.clear()

# 重新预热
warmup()
```

## 验收测试清单

### 1. 三条降级链测试

#### 测试1: 正常流程
```python
# 所有 Provider 正常
result = gateway.invoke("web_search", {"query": "特斯拉 Model 3 价格"})
assert result.ok
assert result.raw["provider_name"] == "baidu_ai_search"
assert result.raw.get("fallback_chain") is None
```

#### 测试2: 一级降级
```python
# 禁用 baidu_ai_search
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=False)

result = gateway.invoke("web_search", {"query": "比亚迪汉 EV 续航"})
assert result.ok
assert result.raw["provider_name"] == "baidu_search"
assert "baidu_ai_search:unavailable" in result.raw["fallback_chain"]
```

#### 测试3: 二级降级
```python
# 禁用 baidu_ai_search 和 baidu_search
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=False)
gateway.update_provider_config("web_search", "baidu_search", enabled=False)

result = gateway.invoke("web_search", {"query": "蔚来 ET7 配置"})
assert result.ok
assert result.raw["provider_name"] == "tavily"
assert len(result.raw["fallback_chain"]) == 2
```

#### 测试4: 全部失败
```python
# 禁用所有 Provider
gateway.update_provider_config("web_search", "baidu_ai_search", enabled=False)
gateway.update_provider_config("web_search", "baidu_search", enabled=False)
gateway.update_provider_config("web_search", "tavily", enabled=False)

result = gateway.invoke("web_search", {"query": "小鹏 P7 价格"})
assert not result.ok
assert "All providers failed" in result.error
assert len(result.raw["fallback_chain"]) == 3
```

### 2. 性能测试

```python
import time

# 测试响应时间
start = time.time()
result = gateway.invoke("web_search", {"query": "理想 L9 多少钱"})
latency = time.time() - start

print(f"响应时间: {latency:.2f}秒")
assert latency < 5.0, "响应时间过长"
```

### 3. 缓存测试

```python
from infra.tool_clients.result_cache import ResultCache

cache = ResultCache()

# 第一次查询（未缓存）
result1 = gateway.invoke("web_search", {"query": "特斯拉 Model 3 价格"})
cache.set("web_search", result1, query="特斯拉 Model 3 价格")

# 第二次查询（命中缓存）
cached = cache.get("web_search", query="特斯拉 Model 3 价格")
assert cached is not None
assert cached.text == result1.text

stats = cache.get_stats()
print(f"缓存命中率: {stats['hit_rate']:.1%}")
```

### 4. 额度监控测试

```python
from infra.tool_clients.quota_monitor import QuotaMonitor

monitor = QuotaMonitor()

# 模拟使用
for _ in range(15):
    monitor.record_usage("baidu_ai_search")

# 检查状态
quota = monitor.get_quota("baidu_ai_search")
print(f"剩余额度: {quota.remaining}/{quota.total_quota}")

# 检查告警
warnings = monitor.check_warnings()
if warnings:
    print("告警:", warnings)
```

## 演示当天检查清单

- [ ] 预热脚本执行成功（20/20）
- [ ] 三条降级链测试通过
- [ ] 响应时间 < 5秒
- [ ] 缓存命中率 > 0%
- [ ] 无额度告警
- [ ] 网络环境稳定
- [ ] 备用方案准备就绪
