# LLM服务集成指南

## 概述

本指南说明如何将新的LLM服务配置系统集成到现有的Agent Service项目中。

## 架构变更

### 旧架构（直接调用）

```
┌─────────────────────────────────────┐
│      Agent Service                  │
│  ┌─────────────────────────────┐   │
│  │ LMStudioClient              │   │
│  │ CozeClient                  │   │
│  │ (硬编码配置)                 │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
         │
         ▼
    推理服务
```

### 新架构（工厂模式 + 配置管理）

```
┌─────────────────────────────────────────────────────────┐
│      Agent Service                                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LLMManager (生产级功能)                           │  │
│  │ - 重试管理                                        │  │
│  │ - 熔断器                                          │  │
│  │ - 监控指标                                        │  │
│  │ - 负载均衡                                        │  │
│  └──────────────────────────────────────────────────┘  │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LLMClientFactory (工厂)                          │  │
│  │ - 创建客户端                                      │  │
│  │ - 单例管理                                        │  │
│  └──────────────────────────────────────────────────┘  │
│           │                                             │
│  ┌────────┴────────┬──────────────┬──────────────┐    │
│  ▼                 ▼              ▼              ▼    │
│ vLLM          Ollama        OpenAI兼容      LMStudio  │
│ Provider      Provider      Provider        Client    │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    推理服务
```

## 集成步骤

### 1. 更新依赖

```bash
# 无需额外依赖，使用标准库
# 如果需要Prometheus指标，可选安装：
pip install prometheus-client
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.llm.example .env.llm

# 编辑配置文件
vim .env.llm

# 加载环境变量
source .env.llm
```

### 3. 更新现有代码

#### 方式A：最小改动（推荐）

保持现有的LMStudioClient和CozeClient不变，新增LLMManager作为可选的高级功能：

```python
# 现有代码保持不变
from agent_service.infra.llm_clients.lm_studio_client import LMStudioClient

client = LMStudioClient()
response = client.generate(query, system_prompt)

# 新代码使用LLMManager
from agent_service.infra.llm_clients.llm_manager import LLMManager

manager = LLMManager()
response = manager.generate(query, system_prompt)
```

#### 方式B：完全迁移

替换所有LLM客户端调用为使用LLMManager：

```python
# 旧代码
from agent_service.infra.llm_clients.lm_studio_client import LMStudioClient
client = LMStudioClient()
response = client.generate(query, system_prompt)

# 新代码
from agent_service.infra.llm_clients.llm_manager import LLMManager
manager = LLMManager()
response = manager.generate(query, system_prompt)
```

### 4. 在关键模块中集成

#### 示例1：Intent Router中集成

```python
# agent_service/domain/intents/unified_router.py

from agent_service.infra.llm_clients.llm_manager import LLMManager

class UnifiedRouter:
    def __init__(self):
        self.llm_manager = LLMManager()
    
    def route_query(self, query: str) -> str:
        """使用LLM进行意图路由"""
        system_prompt = """You are an intent classifier.
        Classify the user query into one of: location, weather, news, finance, trip_planning.
        Return only the intent name."""
        
        try:
            intent = self.llm_manager.generate(query, system_prompt)
            return intent.strip().lower()
        except Exception as e:
            logger.error(f"Intent routing failed: {e}")
            return "unknown"
```

#### 示例2：Trip Planner中集成

```python
# agent_service/domain/trip/engine.py

from agent_service.infra.llm_clients.llm_manager import LLMManager

class TripPlanningEngine:
    def __init__(self):
        self.llm_manager = LLMManager()
    
    def generate_itinerary(self, trip_info: dict) -> str:
        """生成行程计划"""
        system_prompt = """You are a professional trip planner.
        Generate a detailed itinerary based on the provided information."""
        
        user_query = f"""
        Destination: {trip_info['destination']}
        Duration: {trip_info['duration']} days
        Budget: {trip_info['budget']}
        Interests: {', '.join(trip_info['interests'])}
        """
        
        try:
            itinerary = self.llm_manager.generate(user_query, system_prompt)
            return itinerary
        except Exception as e:
            logger.error(f"Itinerary generation failed: {e}")
            raise
```

#### 示例3：Content Rewriter中集成

```python
# agent_service/infra/tool_clients/content_rewriter.py

from agent_service.infra.llm_clients.llm_manager import LLMManager

class ContentRewriter:
    def __init__(self):
        self.llm_manager = LLMManager()
    
    def rewrite_content(self, content: str, style: str) -> str:
        """重写内容"""
        system_prompt = f"""You are a content rewriter.
        Rewrite the content in {style} style while preserving the meaning."""
        
        try:
            rewritten = self.llm_manager.generate(content, system_prompt)
            return rewritten
        except Exception as e:
            logger.error(f"Content rewriting failed: {e}")
            raise
```

### 5. 添加监控和日志

```python
# 在应用启动时初始化
from agent_service.infra.llm_clients.llm_manager import LLMManager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 初始化LLM管理器
llm_manager = LLMManager()

# 定期输出指标
import threading
import time

def log_metrics():
    while True:
        time.sleep(300)  # 每5分钟输出一次
        metrics = llm_manager.get_metrics()
        logger.info(f"LLM Metrics: {metrics}")

metrics_thread = threading.Thread(target=log_metrics, daemon=True)
metrics_thread.start()
```

## 配置场景

### 场景1：开发环境

```bash
# .env.llm
LLM_PROVIDER=lm_studio
LLM_ENVIRONMENT=dev
LLM_BASE_URL=http://localhost:1234
LLM_MODEL_NAME=qwen2.5-7b-instruct-mlx
LLM_TIMEOUT_SEC=120
LLM_CIRCUIT_BREAKER_ENABLED=false
```

### 场景2：测试环境

```bash
# .env.llm
LLM_PROVIDER=ollama
LLM_ENVIRONMENT=staging
LLM_BASE_URL=http://ollama-server:11434
LLM_MODEL_NAME=qwen2.5:7b
LLM_TIMEOUT_SEC=120
LLM_CIRCUIT_BREAKER_ENABLED=true
LLM_CIRCUIT_BREAKER_THRESHOLD=10
```

### 场景3：生产环境

```bash
# .env.llm
LLM_PROVIDER=vllm
LLM_ENVIRONMENT=prod
LLM_BASE_URL=http://vllm-lb:8000
LLM_MODEL_NAME=qwen2.5-7b-instruct
LLM_TIMEOUT_SEC=60
LLM_CIRCUIT_BREAKER_ENABLED=true
LLM_CIRCUIT_BREAKER_THRESHOLD=5
LLM_LOAD_BALANCER_ENABLED=true
LLM_LOAD_BALANCER_STRATEGY=round_robin
LLM_ENABLE_METRICS=true
LLM_ENABLE_LOGGING=true
```

## 测试集成

### 单元测试

```python
# tests/unit/test_llm_integration.py

import pytest
from unittest.mock import patch, Mock

from agent_service.infra.llm_clients.llm_manager import LLMManager
from agent_service.domain.intents.unified_router import UnifiedRouter

class TestLLMIntegration:
    @patch('agent_service.infra.llm_clients.llm_client_factory.LLMClientFactory.create_client')
    def test_router_with_llm_manager(self, mock_create_client):
        # 模拟LLM客户端
        mock_client = Mock()
        mock_client.generate.return_value = "location"
        mock_create_client.return_value = mock_client
        
        # 测试路由
        router = UnifiedRouter()
        intent = router.route_query("Where is the nearest restaurant?")
        
        assert intent == "location"
```

### 集成测试

```python
# tests/integration/test_llm_manager_integration.py

import pytest
import os

from agent_service.infra.llm_clients.llm_manager import LLMManager
from agent_service.infra.llm_clients.llm_config import LLMProvider

@pytest.mark.skipif(
    os.getenv("LLM_PROVIDER") != "lm_studio",
    reason="Requires LM Studio running"
)
class TestLLMManagerIntegration:
    def test_generate_with_real_service(self):
        manager = LLMManager()
        
        response = manager.generate(
            user_query="What is 2+2?",
            system_prompt="You are a helpful assistant."
        )
        
        assert response is not None
        assert len(response) > 0
        assert "4" in response
```

## 迁移检查清单

- [ ] 复制LLM配置文件到项目
- [ ] 更新环境变量配置
- [ ] 在关键模块中集成LLMManager
- [ ] 添加单元测试
- [ ] 添加集成测试
- [ ] 配置监控和日志
- [ ] 文档更新
- [ ] 性能基准测试
- [ ] 生产环境验证

## 常见问题

### Q1: 如何在现有代码中逐步迁移？

**A:** 使用适配器模式：

```python
# 创建适配器，保持向后兼容
class LLMClientAdapter:
    def __init__(self):
        self.manager = LLMManager()
    
    def generate(self, user_query: str, system_prompt: str) -> str:
        return self.manager.generate(user_query, system_prompt)

# 现有代码可以继续使用
client = LLMClientAdapter()
response = client.generate(query, system_prompt)
```

### Q2: 如何处理不同环境的配置？

**A:** 使用环境变量和配置文件：

```python
# config/llm_config.py
import os

LLM_CONFIG = {
    'dev': {
        'provider': 'lm_studio',
        'base_url': 'http://localhost:1234',
    },
    'prod': {
        'provider': 'vllm',
        'base_url': 'http://vllm-lb:8000',
    }
}

env = os.getenv('ENVIRONMENT', 'dev')
config = LLM_CONFIG[env]
```

### Q3: 如何监控LLM服务的性能？

**A:** 使用内置的指标系统：

```python
manager = LLMManager()

# 定期检查指标
metrics = manager.get_metrics()
print(f"Success Rate: {metrics['success_rate']:.2%}")
print(f"Avg Latency: {metrics['avg_latency_ms']:.0f}ms")

# 导出到Prometheus
from prometheus_client import Counter, Histogram
llm_requests = Counter('llm_requests_total', 'Total LLM requests')
llm_latency = Histogram('llm_latency_seconds', 'LLM latency')
```

## 总结

新的LLM服务配置系统提供：

1. **灵活的配置管理** - 支持多种推理框架
2. **生产级功能** - 重试、熔断、监控
3. **易于集成** - 最小改动现有代码
4. **可扩展性** - 支持自定义推理框架
5. **完整的文档** - 部署、运维、故障排查

通过遵循本指南，可以平稳地将项目升级到生产级的LLM服务架构。
