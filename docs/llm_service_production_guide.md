# LLM服务生产级配置指南

## 概述

本指南详细说明如何在生产环境中配置和部署LLM推理服务。系统支持多种推理框架，并提供企业级功能如重试、熔断、监控等。

## 支持的推理框架

### 1. vLLM（推荐用于生产）

**特点：**
- 高吞吐量推理（支持连续批处理）
- 分页注意力机制（降低内存占用）
- 多GPU支持
- 生产级性能

**部署架构：**
```
┌─────────────────────────────────────────┐
│         应用服务（Agent Service）        │
└────────────────┬────────────────────────┘
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────┐
│      负载均衡器（可选）                   │
│   - Round Robin                         │
│   - Least Connections                   │
│   - Health Check                        │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│vLLM-1  │  │vLLM-2  │  │vLLM-3  │
│GPU-0   │  │GPU-0   │  │GPU-0   │
└────────┘  └────────┘  └────────┘
```

**环境变量配置：**
```bash
# 基础配置
LLM_PROVIDER=vllm
LLM_ENVIRONMENT=prod
LLM_BASE_URL=http://vllm-server:8000
LLM_MODEL_NAME=qwen2.5-7b-instruct

# 推理参数
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=512
LLM_TOP_P=0.95
LLM_TOP_K=50

# 重试配置
LLM_RETRY_MAX=3
LLM_RETRY_INITIAL_DELAY=1.0
LLM_RETRY_MAX_DELAY=30.0
LLM_RETRY_BACKOFF=2.0

# 熔断器配置
LLM_CIRCUIT_BREAKER_ENABLED=true
LLM_CIRCUIT_BREAKER_THRESHOLD=5
LLM_CIRCUIT_BREAKER_SUCCESS=2
LLM_CIRCUIT_BREAKER_TIMEOUT=60.0

# 负载均衡配置
LLM_LOAD_BALANCER_ENABLED=true
LLM_LOAD_BALANCER_STRATEGY=round_robin

# 监控和日志
LLM_ENABLE_LOGGING=true
LLM_ENABLE_METRICS=true
LLM_LOG_LEVEL=INFO
LLM_TIMEOUT_SEC=60
```

**vLLM启动命令：**
```bash
# 单GPU部署
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9 \
  --port 8000

# 多GPU部署（张量并行）
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --port 8000

# 使用Ray进行分布式推理
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --tensor-parallel-size 4 \
  --pipeline-parallel-size 2 \
  --port 8000
```

### 2. Ollama（轻量级本地推理）

**特点：**
- 易于部署
- 低资源占用
- 适合开发和小规模生产

**环境变量配置：**
```bash
LLM_PROVIDER=ollama
LLM_ENVIRONMENT=prod
LLM_BASE_URL=http://ollama-server:11434
LLM_MODEL_NAME=qwen2.5:7b
LLM_TIMEOUT_SEC=120
```

**Ollama启动命令：**
```bash
# 启动Ollama服务
ollama serve

# 在另一个终端拉取模型
ollama pull qwen2.5:7b
```

### 3. OpenAI兼容接口

**特点：**
- 支持任何OpenAI兼容的推理框架
- 灵活的部署选项
- 支持云端和本地部署

**环境变量配置：**
```bash
LLM_PROVIDER=openai_compatible
LLM_ENVIRONMENT=prod
LLM_BASE_URL=https://api.openai.com
LLM_API_KEY=sk-xxxxx
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_TIMEOUT_SEC=60
```

## 生产环境最佳实践

### 1. 高可用性部署

**多实例部署：**
```yaml
# Docker Compose示例
version: '3.8'
services:
  vllm-1:
    image: vllm/vllm-openai:latest
    environment:
      - MODEL_NAME=qwen2.5-7b-instruct
      - TENSOR_PARALLEL_SIZE=2
    ports:
      - "8001:8000"
    volumes:
      - model-cache:/root/.cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]

  vllm-2:
    image: vllm/vllm-openai:latest
    environment:
      - MODEL_NAME=qwen2.5-7b-instruct
      - TENSOR_PARALLEL_SIZE=2
    ports:
      - "8002:8000"
    volumes:
      - model-cache:/root/.cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]

  nginx:
    image: nginx:latest
    ports:
      - "8000:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - vllm-1
      - vllm-2

volumes:
  model-cache:
```

**Nginx负载均衡配置：**
```nginx
upstream vllm_backend {
    least_conn;
    server vllm-1:8000 max_fails=3 fail_timeout=30s;
    server vllm-2:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location /v1/chat/completions {
        proxy_pass http://vllm_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering off;
    }
}
```

### 2. 监控和告警

**关键指标：**
- 请求成功率
- 平均响应延迟
- 熔断器状态
- 重试次数
- GPU利用率
- 内存占用

**Prometheus指标导出：**
```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'status']
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration',
    ['provider', 'model']
)

llm_circuit_breaker_state = Gauge(
    'llm_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['provider']
)
```

### 3. 日志配置

**结构化日志示例：**
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'provider': getattr(record, 'provider', 'unknown'),
            'model': getattr(record, 'model', 'unknown'),
            'latency_ms': getattr(record, 'latency_ms', None),
            'status': getattr(record, 'status', 'unknown'),
        }
        return json.dumps(log_data)

# 配置日志
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger('llm_service')
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### 4. 性能优化

**模型优化：**
```bash
# 使用量化模型减少内存占用
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --quantization awq \
  --gpu-memory-utilization 0.95

# 启用分页注意力
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --enable-prefix-caching \
  --gpu-memory-utilization 0.95
```

**连接池配置：**
```python
import urllib.request
from http.client import HTTPConnection

# 启用连接复用
HTTPConnection.debuglevel = 0

# 配置连接池大小
import urllib3
urllib3.disable_warnings()
http = urllib3.PoolManager(
    num_pools=10,
    maxsize=20,
    timeout=urllib3.Timeout(connect=5.0, read=60.0)
)
```

### 5. 故障恢复

**自动故障转移：**
```python
# 配置多个推理服务端点
VLLM_ENDPOINTS = [
    "http://vllm-1:8000",
    "http://vllm-2:8000",
    "http://vllm-3:8000",
]

# 实现故障转移逻辑
class FailoverManager:
    def __init__(self, endpoints):
        self.endpoints = endpoints
        self.current_index = 0
    
    def get_next_endpoint(self):
        endpoint = self.endpoints[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.endpoints)
        return endpoint
```

## 使用示例

### 基础使用

```python
from agent_service.infra.llm_clients.llm_manager import LLMManager

# 创建管理器
manager = LLMManager()

# 生成文本
response = manager.generate(
    user_query="What is the capital of France?",
    system_prompt="You are a helpful assistant."
)

print(response)

# 获取性能指标
metrics = manager.get_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Avg latency: {metrics['avg_latency_ms']:.0f}ms")
```

### 自定义配置

```python
from agent_service.infra.llm_clients.llm_config import (
    LLMServiceConfig,
    LLMProvider,
    Environment,
    RetryConfig,
    CircuitBreakerConfig,
)
from agent_service.infra.llm_clients.llm_manager import LLMManager

# 创建自定义配置
config = LLMServiceConfig(
    provider=LLMProvider.VLLM,
    environment=Environment.PROD,
    base_url="http://vllm-server:8000",
    model_name="qwen2.5-7b-instruct",
    temperature=0.2,
    max_tokens=512,
    retry_config=RetryConfig(
        max_retries=3,
        initial_delay_sec=1.0,
        max_delay_sec=30.0,
    ),
    circuit_breaker_config=CircuitBreakerConfig(
        enabled=True,
        failure_threshold=5,
        success_threshold=2,
    ),
)

# 使用自定义配置创建管理器
manager = LLMManager(config)
response = manager.generate(
    user_query="Hello",
    system_prompt="You are helpful."
)
```

## 故障排查

### 常见问题

**1. 连接超时**
```
症状：timeout error
解决：
- 检查推理服务是否运行
- 增加LLM_TIMEOUT_SEC
- 检查网络连接
```

**2. 熔断器打开**
```
症状：Circuit breaker is OPEN
解决：
- 检查推理服务健康状态
- 查看日志找出根本原因
- 等待熔断器自动恢复（默认60秒）
```

**3. 内存不足**
```
症状：CUDA out of memory
解决：
- 减少batch size
- 使用量化模型
- 增加GPU数量
- 启用分页注意力
```

## 性能基准

基于Qwen2.5-7B-Instruct模型的性能数据：

| 框架 | 吞吐量(req/s) | 延迟(ms) | 内存(GB) | 成本 |
|------|--------------|---------|---------|------|
| vLLM | 50-100 | 100-200 | 16-20 | 低 |
| Ollama | 5-10 | 500-1000 | 8-12 | 低 |
| OpenAI API | 100+ | 200-500 | 0 | 高 |

## 总结

- **开发环境**：使用LM Studio或Ollama
- **小规模生产**：使用Ollama或单实例vLLM
- **大规模生产**：使用多实例vLLM + 负载均衡 + 监控
- **云端部署**：使用OpenAI兼容接口或托管服务
