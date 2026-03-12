# LLM推理源管理 - 快速开始

## 🚀 30秒快速开始

```python
from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

manager = get_inference_source_manager()

# 列出推理源
print(manager.list_sources())

# 切换推理源
manager.switch_source("vllm_prod")

# 生成文本
response = manager.generate("Hello", "You are helpful.")
print(response)
```

## 📋 CLI命令速查

```bash
# 列出所有推理源
python -m agent_service.cli.llm_sources_cli list-sources

# 获取推理源信息
python -m agent_service.cli.llm_sources_cli info vllm_prod

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
  ollama_local ollama http://localhost:11434 qwen2.5:7b
```

## 🔌 REST API速查

```bash
# 列出推理源
curl http://localhost:5000/api/llm/sources

# 获取推理源信息
curl http://localhost:5000/api/llm/sources/vllm_prod

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

## 📝 配置文件格式

```json
{
  "sources": {
    "source_name": {
      "provider": "vllm",
      "base_url": "http://...",
      "model_name": "model",
      "priority": 100,
      "enabled": true
    }
  },
  "default_source": "source_name",
  "failover_enabled": true
}
```

## 🔧 环境变量

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

## 📊 支持的推理框架

| 框架 | 值 | 场景 |
|------|-----|------|
| vLLM | vllm | 生产 |
| Ollama | ollama | 测试 |
| LM Studio | lm_studio | 开发 |
| OpenAI | openai_compatible | 云端 |
| Coze | coze | 云端 |

## 🎯 常用操作

### 切换推理源

```python
manager.switch_source("new_source")
```

### 故障转移

```python
manager.failover_to_next()
```

### 获取状态

```python
sources = manager.list_sources()
metrics = manager.get_metrics()
state = manager.get_circuit_breaker_state()
```

### 启用/禁用

```python
manager.enable_source("source_name")
manager.disable_source("source_name")
```

### 注册新源

```python
from agent_service.infra.llm_clients.llm_config import LLMProvider

manager.register_source(
    name="new_source",
    provider=LLMProvider.VLLM,
    base_url="http://...",
    model_name="model",
    priority=100,
)
```

## 🚨 故障排查

### 推理源连接失败

```bash
# 检查推理源状态
python -m agent_service.cli.llm_sources_cli status

# 检查推理源信息
python -m agent_service.cli.llm_sources_cli info source_name

# 手动测试连接
curl http://source_url/health
```

### 故障转移不工作

```bash
# 检查是否启用故障转移
# 编辑 config/llm_sources.json
# 确保 "failover_enabled": true

# 检查是否有可用的推理源
python -m agent_service.cli.llm_sources_cli list-sources

# 手动执行故障转移
python -m agent_service.cli.llm_sources_cli failover
```

### 性能下降

```bash
# 获取性能指标
python -m agent_service.cli.llm_sources_cli metrics

# 检查熔断器状态
python -m agent_service.cli.llm_sources_cli status

# 切换到其他推理源
python -m agent_service.cli.llm_sources_cli switch other_source
```

## 📚 文档链接

- [完整使用指南](docs/llm_sources_management_guide.md)
- [生产部署检查清单](LLM_SOURCES_PRODUCTION_CHECKLIST.md)
- [实现总结](LLM_SOURCES_IMPLEMENTATION_SUMMARY.md)
- [示例代码](examples/llm_sources_integration_example.py)

## 💡 提示

- 使用配置文件管理推理源
- 启用故障转移提高可靠性
- 定期监控性能指标
- 定期测试故障转移
- 记录详细日志便于调试

---

**快速参考卡** | 打印此页面以便快速查阅
