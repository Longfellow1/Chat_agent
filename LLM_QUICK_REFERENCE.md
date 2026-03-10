# LLM服务快速参考卡

## 🚀 30秒快速开始

```python
from agent_service.infra.llm_clients.llm_manager import LLMManager

# 创建管理器
manager = LLMManager()

# 生成文本
response = manager.generate(
    user_query="What is AI?",
    system_prompt="You are helpful."
)

print(response)
```

## 🔧 环境变量配置

### 最小配置
```bash
export LLM_PROVIDER=lm_studio
export LLM_BASE_URL=http://localhost:1234
export LLM_MODEL_NAME=qwen2.5-7b-instruct-mlx
```

### 完整配置
```bash
# 基础
export LLM_PROVIDER=vllm
export LLM_ENVIRONMENT=prod
export LLM_BASE_URL=http://vllm-server:8000
export LLM_MODEL_NAME=qwen2.5-7b-instruct

# 推理参数
export LLM_TEMPERATURE=0.2
export LLM_MAX_TOKENS=512

# 重试
export LLM_RETRY_MAX=3
export LLM_RETRY_INITIAL_DELAY=1.0

# 熔断器
export LLM_CIRCUIT_BREAKER_ENABLED=true
export LLM_CIRCUIT_BREAKER_THRESHOLD=5

# 监控
export LLM_ENABLE_LOGGING=true
export LLM_ENABLE_METRICS=true
```

## 📊 支持的框架

| 框架 | 环境 | 命令 |
|------|------|------|
| **LM Studio** | 开发 | `LLM_PROVIDER=lm_studio` |
| **Ollama** | 测试 | `LLM_PROVIDER=ollama` |
| **vLLM** | 生产 | `LLM_PROVIDER=vllm` |
| **OpenAI** | 云端 | `LLM_PROVIDER=openai_compatible` |
| **Coze** | 云端 | `LLM_PROVIDER=coze` |

## 💻 常用命令

### 启动推理服务

```bash
# LM Studio (本地)
# 直接启动应用

# Ollama
docker run -d -p 11434:11434 ollama/ollama
ollama pull qwen2.5:7b

# vLLM (单实例)
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model qwen2.5-7b-instruct

# vLLM (集群)
docker-compose -f docker-compose.llm.prod.yml up -d
```

### 测试连接

```bash
# 检查服务
curl http://localhost:8000/health

# 测试推理
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 运行测试

```bash
# 单元测试
pytest tests/unit/test_llm_manager.py -v

# 集成测试
pytest tests/integration/ -v

# 特定测试
pytest tests/unit/test_llm_manager.py::TestLLMMetrics -v
```

## 📈 监控指标

```python
manager = LLMManager()

# 获取指标
metrics = manager.get_metrics()

# 关键指标
print(f"Success Rate: {metrics['success_rate']:.2%}")
print(f"Avg Latency: {metrics['avg_latency_ms']:.0f}ms")
print(f"Total Requests: {metrics['total_requests']}")
print(f"Circuit Breaker: {manager.get_circuit_breaker_state()}")
```

## 🔍 故障排查

### 连接超时
```bash
# 检查服务
curl http://localhost:8000/health

# 增加超时
export LLM_TIMEOUT_SEC=120
```

### 熔断器打开
```bash
# 查看状态
manager.get_circuit_breaker_state()

# 查看日志
docker logs vllm-1 | grep -i error
```

### 内存不足
```bash
# 减少并发
export LLM_MAX_NUM_SEQS=128

# 使用量化模型
--quantization awq
```

## 📚 文档导航

| 文档 | 用途 |
|------|------|
| `LLM_SERVICE_README.md` | 项目总览 |
| `llm_service_production_guide.md` | 部署指南 |
| `llm_deployment_operations.md` | 运维指南 |
| `llm_integration_guide.md` | 集成指南 |
| `LLM_SERVICE_DESIGN_SUMMARY.md` | 深入理解 |

## 🎯 集成步骤

### 1. 配置（5分钟）
```bash
cp .env.llm.example .env.llm
source .env.llm
```

### 2. 导入（1分钟）
```python
from agent_service.infra.llm_clients.llm_manager import LLMManager
```

### 3. 使用（1分钟）
```python
manager = LLMManager()
response = manager.generate(query, system_prompt)
```

### 4. 测试（5分钟）
```bash
pytest tests/unit/test_llm_manager.py -v
```

## 🐳 Docker快速启动

### 开发环境
```bash
# Ollama
docker run -d -p 11434:11434 ollama/ollama
```

### 生产环境
```bash
# 完整环境
docker-compose -f docker-compose.llm.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.llm.prod.yml ps

# 查看日志
docker-compose -f docker-compose.llm.prod.yml logs -f
```

## 🔐 安全配置

### API密钥
```bash
export LLM_API_KEY=sk-xxxxx
```

### 速率限制
```bash
export LLM_RETRY_MAX=3
export LLM_CIRCUIT_BREAKER_THRESHOLD=5
```

### 超时保护
```bash
export LLM_TIMEOUT_SEC=60
```

## 📊 性能对比

| 框架 | 吞吐量 | 延迟 | 内存 |
|------|--------|------|------|
| vLLM | 50-100 | 100-200ms | 16-20GB |
| Ollama | 5-10 | 500-1000ms | 8-12GB |
| LM Studio | 1-5 | 1000-2000ms | 8-12GB |

## 🎓 最佳实践

### ✅ 推荐做法
- 使用环境变量配置
- 启用监控和日志
- 定期检查指标
- 配置熔断器
- 实现错误处理

### ❌ 避免做法
- 硬编码配置
- 忽略异常
- 不监控性能
- 禁用熔断器
- 无日志记录

## 🚨 常见错误

### 错误1：连接拒绝
```
Error: Connection refused
解决：检查推理服务是否运行
```

### 错误2：超时
```
Error: Timeout
解决：增加LLM_TIMEOUT_SEC或检查网络
```

### 错误3：熔断器打开
```
Error: Circuit breaker is OPEN
解决：等待自动恢复或检查服务健康
```

## 📞 获取帮助

1. **查看文档** - 参考相关文档
2. **查看示例** - 参考 `examples/llm_service_example.py`
3. **查看测试** - 参考 `tests/unit/test_llm_manager.py`
4. **查看日志** - 启用详细日志进行调试

## 🔗 相关资源

- vLLM: https://docs.vllm.ai/
- Ollama: https://ollama.ai/
- OpenAI API: https://platform.openai.com/docs/

## 📝 版本信息

- **版本**: 1.0.0
- **发布日期**: 2026年3月10日
- **状态**: 生产就绪 ✅

---

**快速参考卡** | 打印此页面以便快速查阅
