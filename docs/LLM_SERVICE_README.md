# LLM服务生产级配置系统

## 📋 概述

这是一个为Agent Service项目设计的**生产级LLM推理服务配置系统**，支持多种推理框架，提供企业级功能如重试、熔断、监控等。

## 🎯 核心特性

### 1. 多框架支持

| 框架 | 场景 | 特点 |
|------|------|------|
| **vLLM** | 生产环境 | 高吞吐量、多GPU支持、分页注意力 |
| **Ollama** | 测试/小规模 | 轻量级、易部署、低资源占用 |
| **LM Studio** | 开发环境 | 本地推理、易用、支持多种模型 |
| **OpenAI兼容** | 云端部署 | 灵活、支持多个提供商 |
| **Coze** | 云端服务 | 托管服务、无需部署 |

### 2. 生产级功能

```
┌─────────────────────────────────────┐
│      LLMManager                     │
├─────────────────────────────────────┤
│ ✓ 自动重试 (指数退避)               │
│ ✓ 熔断器 (防止级联故障)             │
│ ✓ 性能监控 (实时指标)               │
│ ✓ 负载均衡 (多实例支持)             │
│ ✓ 结构化日志 (便于追踪)             │
│ ✓ 健康检查 (自动恢复)               │
└─────────────────────────────────────┘
```

### 3. 灵活的配置管理

```python
# 从环境变量自动加载
config = LLMServiceConfig.from_env()

# 或自定义配置
config = LLMServiceConfig(
    provider=LLMProvider.VLLM,
    environment=Environment.PROD,
    base_url="http://vllm-server:8000",
    model_name="qwen2.5-7b-instruct",
    # ... 更多配置
)
```

## 📁 项目结构

```
agent_service/infra/llm_clients/
├── base.py                          # LLMClient协议
├── llm_config.py                    # 配置管理
├── llm_client_factory.py            # 工厂模式
├── llm_manager.py                   # 生产级管理器
├── lm_studio_client.py              # LM Studio客户端
├── coze_client.py                   # Coze客户端
└── providers/
    ├── vllm_provider.py             # vLLM提供商
    ├── ollama_provider.py           # Ollama提供商
    └── openai_compatible_provider.py # OpenAI兼容

docs/
├── llm_service_production_guide.md  # 生产部署指南
├── llm_deployment_operations.md     # 运维指南
├── llm_integration_guide.md         # 集成指南
└── LLM_SERVICE_README.md            # 本文件

examples/
└── llm_service_example.py           # 使用示例

tests/unit/
└── test_llm_manager.py              # 单元测试

docker-compose.llm.prod.yml          # 生产部署配置
nginx.conf                           # 负载均衡配置
.env.llm.example                     # 环境变量示例
```

## 🚀 快速开始

### 1. 开发环境

```bash
# 使用LM Studio（本地推理）
export LLM_PROVIDER=lm_studio
export LLM_BASE_URL=http://localhost:1234
export LLM_MODEL_NAME=qwen2.5-7b-instruct-mlx

# 创建管理器并生成文本
from agent_service.infra.llm_clients.llm_manager import LLMManager

manager = LLMManager()
response = manager.generate(
    user_query="Hello, how are you?",
    system_prompt="You are a helpful assistant."
)
print(response)
```

### 2. 测试环境

```bash
# 使用Ollama
docker run -d -p 11434:11434 ollama/ollama
ollama pull qwen2.5:7b

export LLM_PROVIDER=ollama
export LLM_BASE_URL=http://localhost:11434
export LLM_MODEL_NAME=qwen2.5:7b

manager = LLMManager()
response = manager.generate(query, system_prompt)
```

### 3. 生产环境

```bash
# 启动完整的生产环境
docker-compose -f docker-compose.llm.prod.yml up -d

# 配置环境变量
export LLM_PROVIDER=vllm
export LLM_BASE_URL=http://nginx-lb:8000
export LLM_CIRCUIT_BREAKER_ENABLED=true
export LLM_LOAD_BALANCER_ENABLED=true

# 使用管理器
manager = LLMManager()
response = manager.generate(query, system_prompt)

# 监控指标
metrics = manager.get_metrics()
print(f"Success Rate: {metrics['success_rate']:.2%}")
print(f"Avg Latency: {metrics['avg_latency_ms']:.0f}ms")
```

## 📊 架构设计

### 单机部署

```
┌─────────────────────────────────────┐
│      Agent Service                  │
│  ┌─────────────────────────────┐   │
│  │ LLMManager                  │   │
│  │ - 重试                      │   │
│  │ - 熔断器                    │   │
│  │ - 监控                      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
         │ HTTP
         ▼
    ┌────────────────┐
    │  vLLM Server   │
    │  (2x GPU)      │
    └────────────────┘
```

### 集群部署

```
┌─────────────────────────────────────┐
│      Agent Service                  │
│  ┌─────────────────────────────┐   │
│  │ LLMManager                  │   │
│  │ - 重试                      │   │
│  │ - 熔断器                    │   │
│  │ - 负载均衡                  │   │
│  │ - 监控                      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
         │ HTTP
         ▼
    ┌────────────────┐
    │  Nginx LB      │
    │  (负载均衡)     │
    └────────────────┘
     │        │        │
 ┌───▼─┐  ┌───▼──┐  ┌──▼───┐
 │vLLM-1│  │vLLM-2│  │vLLM-3│
 │(4GPU)│  │(4GPU)│  │(4GPU)│
 └──────┘  └──────┘  └──────┘
```

## 🔧 配置参数

### 基础配置

```bash
# 推理框架
LLM_PROVIDER=vllm                    # lm_studio, vllm, ollama, openai_compatible, coze
LLM_ENVIRONMENT=prod                # dev, staging, prod
LLM_BASE_URL=http://vllm-server:8000
LLM_MODEL_NAME=qwen2.5-7b-instruct
LLM_TIMEOUT_SEC=60
```

### 推理参数

```bash
LLM_TEMPERATURE=0.2                 # 0.0-2.0，越低越确定
LLM_MAX_TOKENS=512                  # 最大生成token数
LLM_TOP_P=0.95                      # Top-P采样
LLM_TOP_K=50                        # Top-K采样
```

### 重试配置

```bash
LLM_RETRY_MAX=3                     # 最大重试次数
LLM_RETRY_INITIAL_DELAY=1.0         # 初始延迟（秒）
LLM_RETRY_MAX_DELAY=30.0            # 最大延迟（秒）
LLM_RETRY_BACKOFF=2.0               # 延迟倍增因子
```

### 熔断器配置

```bash
LLM_CIRCUIT_BREAKER_ENABLED=true    # 是否启用
LLM_CIRCUIT_BREAKER_THRESHOLD=5     # 失败阈值
LLM_CIRCUIT_BREAKER_SUCCESS=2       # 恢复阈值
LLM_CIRCUIT_BREAKER_TIMEOUT=60.0    # 打开时长（秒）
```

### 负载均衡配置

```bash
LLM_LOAD_BALANCER_ENABLED=true      # 是否启用
LLM_LOAD_BALANCER_STRATEGY=round_robin  # round_robin, least_connections, random
```

## 📈 性能指标

基于Qwen2.5-7B-Instruct的性能数据：

| 指标 | vLLM | Ollama | LM Studio |
|------|------|--------|-----------|
| 吞吐量 | 50-100 req/s | 5-10 req/s | 1-5 req/s |
| 延迟 | 100-200ms | 500-1000ms | 1000-2000ms |
| 内存 | 16-20GB | 8-12GB | 8-12GB |
| 成本 | 低 | 低 | 低 |

## 🛠️ 使用示例

### 基础使用

```python
from agent_service.infra.llm_clients.llm_manager import LLMManager

manager = LLMManager()
response = manager.generate(
    user_query="What is the capital of France?",
    system_prompt="You are a helpful assistant."
)
print(response)
```

### 自定义配置

```python
from agent_service.infra.llm_clients.llm_config import (
    LLMServiceConfig,
    LLMProvider,
    Environment,
)

config = LLMServiceConfig(
    provider=LLMProvider.VLLM,
    environment=Environment.PROD,
    base_url="http://vllm-server:8000",
    model_name="qwen2.5-7b-instruct",
    temperature=0.2,
    max_tokens=512,
)

manager = LLMManager(config)
response = manager.generate(query, system_prompt)
```

### 监控指标

```python
manager = LLMManager()

# 生成多个请求
for query in queries:
    response = manager.generate(query, system_prompt)

# 获取聚合指标
metrics = manager.get_metrics()
print(f"Success Rate: {metrics['success_rate']:.2%}")
print(f"Avg Latency: {metrics['avg_latency_ms']:.0f}ms")
print(f"Total Requests: {metrics['total_requests']}")
```

## 📚 文档

- **[生产部署指南](./llm_service_production_guide.md)** - 详细的部署和配置说明
- **[运维指南](./llm_deployment_operations.md)** - 监控、告警、故障排查
- **[集成指南](./llm_integration_guide.md)** - 如何集成到现有项目
- **[使用示例](../examples/llm_service_example.py)** - 完整的代码示例

## 🧪 测试

```bash
# 运行单元测试
pytest tests/unit/test_llm_manager.py -v

# 运行集成测试
pytest tests/integration/test_llm_manager_integration.py -v

# 运行特定测试
pytest tests/unit/test_llm_manager.py::TestLLMMetrics -v
```

## 🐳 Docker部署

### 开发环境

```bash
# 使用LM Studio
docker run -d -p 1234:1234 lmstudio/lmstudio:latest
```

### 测试环境

```bash
# 使用Ollama
docker run -d -p 11434:11434 ollama/ollama
```

### 生产环境

```bash
# 启动完整的生产环境
docker-compose -f docker-compose.llm.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.llm.prod.yml ps

# 查看日志
docker-compose -f docker-compose.llm.prod.yml logs -f
```

## 🔍 故障排查

### 连接超时

```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 增加超时时间
export LLM_TIMEOUT_SEC=120
```

### 熔断器打开

```bash
# 检查推理服务日志
docker logs vllm-1

# 查看熔断器状态
manager.get_circuit_breaker_state()
```

### 内存不足

```bash
# 减少并发数
export LLM_MAX_NUM_SEQS=128

# 使用量化模型
--quantization awq
```

## 📋 集成检查清单

- [ ] 复制LLM配置文件
- [ ] 更新环境变量
- [ ] 在关键模块集成LLMManager
- [ ] 添加单元测试
- [ ] 添加集成测试
- [ ] 配置监控和日志
- [ ] 文档更新
- [ ] 性能基准测试
- [ ] 生产环境验证

## 🎓 最佳实践

### 1. 开发环境

- 使用LM Studio或Ollama
- 禁用熔断器
- 增加超时时间
- 启用详细日志

### 2. 测试环境

- 使用Ollama或单实例vLLM
- 启用熔断器
- 配置重试机制
- 监控性能指标

### 3. 生产环境

- 使用多实例vLLM集群
- 配置Nginx负载均衡
- 启用所有生产级功能
- 配置监控和告警
- 定期备份和升级

## 🤝 贡献

欢迎提交问题和改进建议。

## 📄 许可证

MIT License

## 📞 支持

如有问题，请参考文档或提交Issue。

---

**最后更新**: 2026年3月10日
**版本**: 1.0.0
