# LLM推理服务部署和运维指南

## 快速开始

### 1. 开发环境（本地）

```bash
# 使用LM Studio
export LLM_PROVIDER=lm_studio
export LLM_ENVIRONMENT=dev
export LLM_BASE_URL=http://localhost:1234
export LLM_MODEL_NAME=qwen2.5-7b-instruct-mlx

# 或使用Ollama
export LLM_PROVIDER=ollama
export LLM_ENVIRONMENT=dev
export LLM_BASE_URL=http://localhost:11434
export LLM_MODEL_NAME=qwen2.5:7b
```

### 2. 测试环境（单实例vLLM）

```bash
# 启动vLLM
docker run --gpus all \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model qwen2.5-7b-instruct \
  --tensor-parallel-size 2

# 配置环境变量
export LLM_PROVIDER=vllm
export LLM_ENVIRONMENT=staging
export LLM_BASE_URL=http://localhost:8000
export LLM_MODEL_NAME=qwen2.5-7b-instruct
```

### 3. 生产环境（多实例集群）

```bash
# 启动完整的生产环境
docker-compose -f docker-compose.llm.prod.yml up -d

# 验证服务状态
docker-compose -f docker-compose.llm.prod.yml ps

# 查看日志
docker-compose -f docker-compose.llm.prod.yml logs -f nginx
docker-compose -f docker-compose.llm.prod.yml logs -f vllm-1
```

## 部署架构

### 单机部署

```
┌─────────────────────────────────────────┐
│         应用服务（Agent Service）        │
└────────────────┬────────────────────────┘
                 │ HTTP
                 ▼
        ┌────────────────┐
        │  vLLM Server   │
        │  (2x GPU)      │
        └────────────────┘
```

**配置：**
```bash
LLM_BASE_URL=http://localhost:8000
LLM_TENSOR_PARALLEL_SIZE=2
```

### 多机集群部署

```
┌─────────────────────────────────────────┐
│         应用服务（Agent Service）        │
└────────────────┬────────────────────────┘
                 │ HTTP
                 ▼
        ┌────────────────┐
        │  Nginx LB      │
        │  (负载均衡)     │
        └────────────────┘
         │        │        │
    ┌────▼─┐  ┌───▼──┐  ┌──▼───┐
    │vLLM-1│  │vLLM-2│  │vLLM-3│
    │(4GPU)│  │(4GPU)│  │(4GPU)│
    └──────┘  └──────┘  └──────┘
```

**配置：**
```bash
LLM_BASE_URL=http://nginx-lb:8000
LLM_LOAD_BALANCER_ENABLED=true
LLM_LOAD_BALANCER_STRATEGY=round_robin
```

## 性能调优

### 1. vLLM参数优化

```bash
# 基础配置
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --max-num-seqs 256 \
  --max-model-len 4096 \
  --enable-prefix-caching \
  --port 8000

# 参数说明
# --tensor-parallel-size: 张量并行度（GPU数量）
# --gpu-memory-utilization: GPU内存利用率（0.0-1.0）
# --max-num-seqs: 最大并发序列数
# --max-model-len: 最大模型长度
# --enable-prefix-caching: 启用前缀缓存
```

### 2. 内存优化

```bash
# 使用量化模型
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --quantization awq \
  --gpu-memory-utilization 0.95

# 使用GPTQ量化
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct-gptq \
  --quantization gptq \
  --gpu-memory-utilization 0.95
```

### 3. 吞吐量优化

```bash
# 启用连续批处理
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --enable-chunked-prefill \
  --max-num-seqs 512 \
  --max-num-batched-tokens 8192

# 启用分页注意力
python -m vllm.entrypoints.openai.api_server \
  --model qwen2.5-7b-instruct \
  --enable-prefix-caching \
  --block-size 16
```

## 监控和告警

### 1. 关键指标

```python
# 应用层指标
- llm_requests_total: 总请求数
- llm_requests_success: 成功请求数
- llm_requests_failed: 失败请求数
- llm_request_duration_seconds: 请求延迟
- llm_circuit_breaker_state: 熔断器状态
- llm_retry_count: 重试次数

# 系统层指标
- gpu_utilization: GPU利用率
- gpu_memory_used: GPU内存使用
- vllm_num_requests_running: 运行中的请求数
- vllm_num_requests_waiting: 等待中的请求数
- vllm_cache_usage: 缓存使用率
```

### 2. Prometheus告警规则

```yaml
# prometheus-rules.yml
groups:
  - name: llm_service
    rules:
      # 高错误率告警
      - alert: HighLLMErrorRate
        expr: |
          (1 - (llm_requests_success / llm_requests_total)) > 0.05
        for: 5m
        annotations:
          summary: "LLM服务错误率过高"
          description: "错误率: {{ $value | humanizePercentage }}"

      # 熔断器打开告警
      - alert: LLMCircuitBreakerOpen
        expr: llm_circuit_breaker_state == 1
        for: 1m
        annotations:
          summary: "LLM熔断器打开"
          description: "推理服务可能不可用"

      # 高延迟告警
      - alert: HighLLMLatency
        expr: |
          histogram_quantile(0.95, llm_request_duration_seconds) > 5
        for: 5m
        annotations:
          summary: "LLM服务延迟过高"
          description: "P95延迟: {{ $value }}秒"

      # GPU内存告警
      - alert: HighGPUMemoryUsage
        expr: gpu_memory_used / gpu_memory_total > 0.95
        for: 5m
        annotations:
          summary: "GPU内存使用过高"
          description: "使用率: {{ $value | humanizePercentage }}"
```

### 3. 日志聚合

```bash
# 使用ELK Stack
docker run -d \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# 配置Filebeat收集日志
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/vllm/*.log
    - /var/log/nginx/*.log

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

## 故障排查

### 1. 服务无法启动

```bash
# 检查GPU可用性
nvidia-smi

# 检查模型文件
ls ~/.cache/huggingface/hub/

# 查看启动日志
docker logs vllm-1

# 常见原因：
# - GPU驱动问题
# - 模型文件损坏
# - 内存不足
```

### 2. 请求超时

```bash
# 检查服务响应
curl -v http://localhost:8000/v1/models

# 检查网络连接
ping vllm-server

# 增加超时时间
export LLM_TIMEOUT_SEC=120

# 常见原因：
# - 模型加载缓慢
# - 网络延迟
# - 服务过载
```

### 3. 内存溢出

```bash
# 检查GPU内存
nvidia-smi

# 减少并发数
export LLM_MAX_NUM_SEQS=128

# 使用量化模型
--quantization awq

# 常见原因：
# - 模型过大
# - 并发数过高
# - 内存泄漏
```

### 4. 熔断器频繁打开

```bash
# 检查推理服务健康状态
curl http://localhost:8000/health

# 查看错误日志
docker logs vllm-1 | grep -i error

# 调整熔断器参数
export LLM_CIRCUIT_BREAKER_THRESHOLD=10
export LLM_CIRCUIT_BREAKER_TIMEOUT=120

# 常见原因：
# - 推理服务不稳定
# - 网络问题
# - 资源不足
```

## 升级和维护

### 1. 模型升级

```bash
# 拉取新模型
ollama pull qwen2.5:14b

# 更新配置
export LLM_MODEL_NAME=qwen2.5:14b

# 重启服务
docker-compose -f docker-compose.llm.prod.yml restart vllm-1
```

### 2. 版本升级

```bash
# 更新vLLM镜像
docker pull vllm/vllm-openai:latest

# 滚动升级
docker-compose -f docker-compose.llm.prod.yml up -d --no-deps --build vllm-1
docker-compose -f docker-compose.llm.prod.yml up -d --no-deps --build vllm-2
docker-compose -f docker-compose.llm.prod.yml up -d --no-deps --build vllm-3
```

### 3. 备份和恢复

```bash
# 备份模型缓存
docker run --rm -v model-cache:/data \
  -v /backup:/backup \
  alpine tar czf /backup/model-cache.tar.gz -C /data .

# 恢复模型缓存
docker run --rm -v model-cache:/data \
  -v /backup:/backup \
  alpine tar xzf /backup/model-cache.tar.gz -C /data
```

## 成本优化

### 1. 资源利用率

```bash
# 监控GPU利用率
watch -n 1 nvidia-smi

# 调整并发数以平衡延迟和吞吐量
export LLM_MAX_NUM_SEQS=256

# 启用模型缓存
export LLM_ENABLE_PREFIX_CACHING=1
```

### 2. 自动扩缩容

```yaml
# Kubernetes HPA配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 安全性

### 1. API认证

```python
# 添加API密钥验证
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('LLM_API_KEY'):
            return {'error': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated_function
```

### 2. 速率限制

```python
# 使用Flask-Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/v1/chat/completions')
@limiter.limit("10 per minute")
def chat_completions():
    pass
```

### 3. 输入验证

```python
# 验证请求内容
def validate_request(data):
    if not isinstance(data.get('messages'), list):
        raise ValueError("Invalid messages format")
    
    if len(data.get('messages', [])) == 0:
        raise ValueError("Messages cannot be empty")
    
    if data.get('max_tokens', 512) > 4096:
        raise ValueError("max_tokens exceeds limit")
```

## 总结

- **开发**：使用LM Studio或Ollama快速迭代
- **测试**：单实例vLLM验证功能
- **生产**：多实例vLLM + Nginx负载均衡 + 监控告警
- **运维**：定期监控、备份、升级和优化
