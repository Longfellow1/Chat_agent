# LLM推理源管理指南

## 概述

这是一个完整的推理源管理系统，支持：

- ✅ 多推理源配置和管理
- ✅ 动态切换推理源
- ✅ 自动故障转移
- ✅ 实时性能监控
- ✅ REST API接口
- ✅ CLI命令行工具
- ✅ 生产级可靠性

## 快速开始

### 1. 配置推理源

编辑 `config/llm_sources.json`:

```json
{
  "sources": {
    "lm_studio_local": {
      "provider": "lm_studio",
      "base_url": "http://localhost:1234",
      "model_name": "qwen2.5-7b-instruct-mlx",
      "priority": 100,
      "enabled": true
    },
    "vllm_prod": {
      "provider": "vllm",
      "base_url": "http://vllm-server:8000",
      "model_name": "qwen2.5-7b-instruct",
      "priority": 90,
      "enabled": true
    }
  },
  "default_source": "lm_studio_local",
  "failover_enabled": true
}
```

### 2. 使用推理源管理器

```python
from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

# 获取管理器
manager = get_inference_source_manager()

# 列出所有推理源
sources = manager.list_sources()
print(sources)

# 切换推理源
manager.switch_source("vllm_prod")

# 生成文本
response = manager.generate(
    user_query="Hello",
    system_prompt="You are helpful."
)
print(response)

# 获取指标
metrics = manager.get_metrics()
print(metrics)
```

### 3. 使用CLI工具

```bash
# 列出所有推理源
python -m agent_service.cli.llm_sources_cli list-sources

# 获取推理源信息
python -m agent_service.cli.llm_sources_cli info lm_studio_local

# 切换推理源
python -m agent_service.cli.llm_sources_cli switch vllm_prod

# 启用/禁用推理源
python -m agent_service.cli.llm_sources_cli enable vllm_prod
python -m agent_service.cli.llm_sources_cli disable lm_studio_local

# 执行故障转移
python -m agent_service.cli.llm_sources_cli failover

# 获取状态
python -m agent_service.cli.llm_sources_cli status

# 生成文本
python -m agent_service.cli.llm_sources_cli generate "What is AI?"

# 获取指标
python -m agent_service.cli.llm_sources_cli metrics

# 注册新推理源
python -m agent_service.cli.llm_sources_cli register \
  ollama_local ollama http://localhost:11434 qwen2.5:7b \
  --priority 80 --enabled true
```

### 4. 使用REST API

```bash
# 列出所有推理源
curl http://localhost:5000/api/llm/sources

# 获取推理源信息
curl http://localhost:5000/api/llm/sources/lm_studio_local

# 切换推理源
curl -X POST http://localhost:5000/api/llm/sources/vllm_prod/switch

# 启用/禁用推理源
curl -X POST http://localhost:5000/api/llm/sources/vllm_prod/enable
curl -X POST http://localhost:5000/api/llm/sources/lm_studio_local/disable

# 执行故障转移
curl -X POST http://localhost:5000/api/llm/failover

# 获取指标
curl http://localhost:5000/api/llm/metrics

# 获取状态
curl http://localhost:5000/api/llm/status
```

## 配置详解

### 推理源配置

```json
{
  "sources": {
    "source_name": {
      "provider": "vllm",              // 推理框架
      "base_url": "http://...",        // 服务地址
      "model_name": "model",           // 模型名称
      "priority": 100,                 // 优先级（高优先级优先使用）
      "enabled": true,                 // 是否启用
      "api_key": "${API_KEY}",         // API密钥（支持环境变量）
      "environment": "prod"            // 环境标签
    }
  },
  "default_source": "source_name",     // 默认推理源
  "failover_enabled": true,            // 是否启用故障转移
  "failover_strategy": "priority"      // 故障转移策略
}
```

### 环境变量配置

```bash
# 基础配置
export LLM_PROVIDER=vllm
export LLM_BASE_URL=http://vllm-server:8000
export LLM_MODEL_NAME=qwen2.5-7b-instruct

# 推理源配置文件
export LLM_SOURCES_CONFIG=config/llm_sources.json

# 环境
export LLM_ENVIRONMENT=prod
```

## 生产环境部署

### 1. 多推理源配置

```json
{
  "sources": {
    "vllm_prod_1": {
      "provider": "vllm",
      "base_url": "http://vllm-1:8000",
      "model_name": "qwen2.5-7b-instruct",
      "priority": 100,
      "enabled": true
    },
    "vllm_prod_2": {
      "provider": "vllm",
      "base_url": "http://vllm-2:8000",
      "model_name": "qwen2.5-7b-instruct",
      "priority": 90,
      "enabled": true
    },
    "vllm_prod_3": {
      "provider": "vllm",
      "base_url": "http://vllm-3:8000",
      "model_name": "qwen2.5-7b-instruct",
      "priority": 80,
      "enabled": true
    },
    "ollama_fallback": {
      "provider": "ollama",
      "base_url": "http://ollama-fallback:11434",
      "model_name": "qwen2.5:7b",
      "priority": 50,
      "enabled": true
    }
  },
  "default_source": "vllm_prod_1",
  "failover_enabled": true,
  "failover_strategy": "priority"
}
```

### 2. 故障转移流程

```
请求失败 → 检查熔断器
         → 如果打开 → 故障转移到下一个源
         → 按优先级选择可用源
         → 重试请求
         → 成功 → 返回结果
         → 失败 → 继续转移
```

### 3. 监控和告警

```python
# 定期检查推理源状态
import time
from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

manager = get_inference_source_manager()

while True:
    metrics = manager.get_metrics()
    
    # 检查成功率
    if metrics['success_rate'] < 0.95:
        alert("Low success rate")
    
    # 检查延迟
    if metrics['avg_latency_ms'] > 1000:
        alert("High latency")
    
    # 检查熔断器
    if manager.get_circuit_breaker_state() == "open":
        alert("Circuit breaker open")
    
    time.sleep(60)
```

## 集成到现有代码

### 方式1：直接使用管理器

```python
from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

manager = get_inference_source_manager()
response = manager.generate(query, system_prompt)
```

### 方式2：在Intent Router中集成

```python
from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

class UnifiedRouter:
    def __init__(self):
        self.llm_manager = get_inference_source_manager()
    
    def route_query(self, query: str) -> str:
        system_prompt = "You are an intent classifier..."
        intent = self.llm_manager.generate(query, system_prompt)
        return intent.strip().lower()
```

### 方式3：在Trip Planner中集成

```python
from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

class TripPlanningEngine:
    def __init__(self):
        self.llm_manager = get_inference_source_manager()
    
    def generate_itinerary(self, trip_info: dict) -> str:
        system_prompt = "You are a professional trip planner..."
        user_query = f"Generate itinerary for {trip_info['destination']}"
        return self.llm_manager.generate(user_query, system_prompt)
```

## 故障排查

### 问题1：推理源连接失败

```bash
# 检查推理源状态
python -m agent_service.cli.llm_sources_cli status

# 检查推理源信息
python -m agent_service.cli.llm_sources_cli info source_name

# 手动测试连接
curl http://source_url/health
```

### 问题2：故障转移不工作

```bash
# 检查是否启用故障转移
# 编辑 config/llm_sources.json
# 确保 "failover_enabled": true

# 检查是否有可用的推理源
python -m agent_service.cli.llm_sources_cli list-sources

# 手动执行故障转移
python -m agent_service.cli.llm_sources_cli failover
```

### 问题3：性能指标异常

```bash
# 获取详细指标
python -m agent_service.cli.llm_sources_cli metrics

# 检查熔断器状态
python -m agent_service.cli.llm_sources_cli status

# 如果熔断器打开，等待自动恢复或手动切换源
python -m agent_service.cli.llm_sources_cli switch other_source
```

## 最佳实践

### 1. 配置管理

- ✅ 使用配置文件管理推理源
- ✅ 使用环境变量覆盖敏感信息
- ✅ 为不同环境使用不同配置
- ❌ 不要硬编码推理源地址

### 2. 故障转移

- ✅ 启用故障转移
- ✅ 配置多个推理源
- ✅ 设置合理的优先级
- ✅ 定期测试故障转移
- ❌ 不要依赖单一推理源

### 3. 监控

- ✅ 定期检查推理源状态
- ✅ 监控性能指标
- ✅ 配置告警规则
- ✅ 记录详细日志
- ❌ 不要忽视性能下降

### 4. 生产部署

- ✅ 使用多个推理源
- ✅ 配置负载均衡
- ✅ 启用熔断器
- ✅ 配置监控告警
- ✅ 定期备份配置
- ❌ 不要在生产环境进行大的变更

## 性能对比

| 推理源 | 吞吐量 | 延迟 | 可靠性 |
|--------|--------|------|--------|
| vLLM集群 | 150-300 req/s | 100-200ms | 99.9% |
| Ollama | 5-10 req/s | 500-1000ms | 99% |
| LM Studio | 1-5 req/s | 1000-2000ms | 95% |

## 总结

这个推理源管理系统提供了：

1. **灵活的配置** - 支持多种推理框架和部署方式
2. **动态切换** - 无需重启即可切换推理源
3. **自动故障转移** - 推理源故障时自动转移
4. **完整的监控** - 实时性能指标和状态监控
5. **多种接口** - CLI、API、Python SDK
6. **生产级可靠性** - 熔断器、重试、日志等

可以直接用于生产环境，支持随时切换推理源。
