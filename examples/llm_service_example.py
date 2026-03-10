"""LLM服务使用示例"""

import os
import sys
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_service.infra.llm_clients.llm_manager import LLMManager
from agent_service.infra.llm_clients.llm_config import (
    LLMServiceConfig,
    LLMProvider,
    Environment,
    RetryConfig,
    CircuitBreakerConfig,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """示例1：基础使用 - 从环境变量加载配置"""
    print("\n" + "="*60)
    print("示例1：基础使用")
    print("="*60)
    
    # 从环境变量加载配置
    manager = LLMManager()
    
    # 生成文本
    response = manager.generate(
        user_query="What is the capital of France?",
        system_prompt="You are a helpful assistant."
    )
    
    print(f"Query: What is the capital of France?")
    print(f"Response: {response}")
    
    # 显示性能指标
    metrics = manager.get_metrics()
    print(f"\nMetrics:")
    print(f"  Success Rate: {metrics['success_rate']:.2%}")
    print(f"  Avg Latency: {metrics['avg_latency_ms']:.0f}ms")
    print(f"  Total Requests: {metrics['total_requests']}")


def example_2_custom_config():
    """示例2：自定义配置 - vLLM生产环境"""
    print("\n" + "="*60)
    print("示例2：自定义配置 - vLLM生产环境")
    print("="*60)
    
    # 创建自定义配置
    config = LLMServiceConfig(
        provider=LLMProvider.VLLM,
        environment=Environment.PROD,
        base_url="http://vllm-server:8000",
        model_name="qwen2.5-7b-instruct",
        temperature=0.2,
        max_tokens=512,
        timeout_sec=60,
        retry_config=RetryConfig(
            max_retries=3,
            initial_delay_sec=1.0,
            max_delay_sec=30.0,
            backoff_multiplier=2.0,
        ),
        circuit_breaker_config=CircuitBreakerConfig(
            enabled=True,
            failure_threshold=5,
            success_threshold=2,
            timeout_sec=60.0,
        ),
        enable_logging=True,
        enable_metrics=True,
    )
    
    # 使用自定义配置创建管理器
    manager = LLMManager(config)
    
    print(f"Configuration:")
    print(f"  Provider: {config.provider.value}")
    print(f"  Environment: {config.environment.value}")
    print(f"  Base URL: {config.base_url}")
    print(f"  Model: {config.model_name}")
    print(f"  Temperature: {config.temperature}")
    print(f"  Max Tokens: {config.max_tokens}")
    
    # 生成文本
    try:
        response = manager.generate(
            user_query="Explain quantum computing in simple terms",
            system_prompt="You are an expert in quantum computing."
        )
        print(f"\nResponse: {response}")
    except Exception as e:
        print(f"Error: {e}")


def example_3_ollama_local():
    """示例3：本地Ollama部署"""
    print("\n" + "="*60)
    print("示例3：本地Ollama部署")
    print("="*60)
    
    config = LLMServiceConfig(
        provider=LLMProvider.OLLAMA,
        environment=Environment.DEV,
        base_url="http://localhost:11434",
        model_name="qwen2.5:7b",
        temperature=0.3,
        timeout_sec=120,
    )
    
    manager = LLMManager(config)
    
    print(f"Configuration:")
    print(f"  Provider: {config.provider.value}")
    print(f"  Base URL: {config.base_url}")
    print(f"  Model: {config.model_name}")
    
    try:
        response = manager.generate(
            user_query="Tell me a joke",
            system_prompt="You are a funny assistant."
        )
        print(f"\nResponse: {response}")
    except Exception as e:
        print(f"Error: {e}")


def example_4_openai_compatible():
    """示例4：OpenAI兼容接口"""
    print("\n" + "="*60)
    print("示例4：OpenAI兼容接口")
    print("="*60)
    
    config = LLMServiceConfig(
        provider=LLMProvider.OPENAI_COMPATIBLE,
        environment=Environment.PROD,
        base_url="https://api.openai.com",
        api_key=os.getenv("OPENAI_API_KEY", "sk-xxxxx"),
        model_name="gpt-3.5-turbo",
        temperature=0.2,
        max_tokens=512,
        timeout_sec=60,
    )
    
    manager = LLMManager(config)
    
    print(f"Configuration:")
    print(f"  Provider: {config.provider.value}")
    print(f"  Base URL: {config.base_url}")
    print(f"  Model: {config.model_name}")
    
    try:
        response = manager.generate(
            user_query="What is machine learning?",
            system_prompt="You are an AI expert."
        )
        print(f"\nResponse: {response}")
    except Exception as e:
        print(f"Error: {e}")


def example_5_monitoring():
    """示例5：监控和指标"""
    print("\n" + "="*60)
    print("示例5：监控和指标")
    print("="*60)
    
    config = LLMServiceConfig(
        provider=LLMProvider.VLLM,
        environment=Environment.PROD,
        base_url="http://vllm-server:8000",
        model_name="qwen2.5-7b-instruct",
        enable_metrics=True,
        enable_logging=True,
    )
    
    manager = LLMManager(config)
    
    # 模拟多个请求
    queries = [
        "What is AI?",
        "Explain deep learning",
        "What is NLP?",
    ]
    
    for query in queries:
        try:
            response = manager.generate(
                user_query=query,
                system_prompt="You are helpful."
            )
            print(f"Query: {query}")
            print(f"Response: {response[:50]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    # 显示聚合指标
    metrics = manager.get_metrics()
    print(f"\nAggregated Metrics:")
    print(f"  Total Requests: {metrics['total_requests']}")
    print(f"  Successful: {metrics['successful_requests']}")
    print(f"  Failed: {metrics['failed_requests']}")
    print(f"  Success Rate: {metrics['success_rate']:.2%}")
    print(f"  Avg Latency: {metrics['avg_latency_ms']:.0f}ms")
    print(f"  Circuit Breaker State: {manager.get_circuit_breaker_state()}")


def example_6_error_handling():
    """示例6：错误处理和重试"""
    print("\n" + "="*60)
    print("示例6：错误处理和重试")
    print("="*60)
    
    config = LLMServiceConfig(
        provider=LLMProvider.VLLM,
        environment=Environment.PROD,
        base_url="http://invalid-server:8000",  # 无效的服务器
        model_name="qwen2.5-7b-instruct",
        retry_config=RetryConfig(
            max_retries=2,
            initial_delay_sec=0.5,
        ),
        circuit_breaker_config=CircuitBreakerConfig(
            enabled=True,
            failure_threshold=3,
        ),
    )
    
    manager = LLMManager(config)
    
    print(f"Configuration:")
    print(f"  Base URL: {config.base_url}")
    print(f"  Max Retries: {config.retry_config.max_retries}")
    print(f"  Circuit Breaker Enabled: {config.circuit_breaker_config.enabled}")
    
    try:
        response = manager.generate(
            user_query="Hello",
            system_prompt="You are helpful."
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error (expected): {type(e).__name__}: {e}")
        print(f"Circuit Breaker State: {manager.get_circuit_breaker_state()}")


if __name__ == "__main__":
    print("LLM Service Examples")
    print("=" * 60)
    
    # 运行示例
    # example_1_basic_usage()
    # example_2_custom_config()
    # example_3_ollama_local()
    # example_4_openai_compatible()
    # example_5_monitoring()
    # example_6_error_handling()
    
    print("\n提示：取消注释上面的示例函数调用来运行特定示例")
    print("\n环境变量配置示例：")
    print("  export LLM_PROVIDER=vllm")
    print("  export LLM_ENVIRONMENT=prod")
    print("  export LLM_BASE_URL=http://vllm-server:8000")
    print("  export LLM_MODEL_NAME=qwen2.5-7b-instruct")
