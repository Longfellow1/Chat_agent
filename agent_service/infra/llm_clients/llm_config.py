"""LLM服务配置管理 - 支持多种推理框架和生产环境"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class LLMProvider(Enum):
    """支持的LLM推理框架"""
    LM_STUDIO = "lm_studio"  # 本地开发
    VLLM = "vllm"  # 高性能推理框架
    OLLAMA = "ollama"  # 轻量级推理
    COZE = "coze"  # 云端服务
    OPENAI_COMPATIBLE = "openai_compatible"  # OpenAI兼容接口
    CUSTOM = "custom"  # 自定义推理框架


class Environment(Enum):
    """运行环境"""
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    initial_delay_sec: float = 1.0
    max_delay_sec: float = 30.0
    backoff_multiplier: float = 2.0
    retry_on_timeout: bool = True
    retry_on_rate_limit: bool = True


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    enabled: bool = True
    failure_threshold: int = 5  # 失败次数阈值
    success_threshold: int = 2  # 恢复成功次数
    timeout_sec: float = 60.0  # 熔断器打开时长


@dataclass
class LoadBalancerConfig:
    """负载均衡配置"""
    enabled: bool = False
    strategy: str = "round_robin"  # round_robin, least_connections, random
    health_check_interval_sec: int = 30
    health_check_timeout_sec: int = 5


@dataclass
class LLMServiceConfig:
    """LLM服务配置"""
    provider: LLMProvider
    environment: Environment
    
    # 基础连接配置
    base_url: str
    api_key: Optional[str] = None
    model_name: str = ""
    timeout_sec: float = 60.0
    
    # 推理参数
    temperature: float = 0.2
    max_tokens: int = 512
    top_p: float = 0.95
    top_k: int = 50
    
    # 高级配置
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker_config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    load_balancer_config: LoadBalancerConfig = field(default_factory=LoadBalancerConfig)
    
    # 自定义参数
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    # 监控和日志
    enable_logging: bool = True
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> LLMServiceConfig:
        """从环境变量加载配置"""
        provider_str = os.getenv("LLM_PROVIDER", "lm_studio").lower()
        environment_str = os.getenv("LLM_ENVIRONMENT", "dev").lower()
        
        try:
            provider = LLMProvider(provider_str)
            environment = Environment(environment_str)
        except ValueError as e:
            raise ValueError(f"Invalid LLM_PROVIDER or LLM_ENVIRONMENT: {e}")
        
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:1234")
        api_key = os.getenv("LLM_API_KEY")
        model_name = os.getenv("LLM_MODEL_NAME", "qwen2.5-7b-instruct-mlx")
        timeout_sec = float(os.getenv("LLM_TIMEOUT_SEC", "60"))
        
        # 推理参数
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "512"))
        top_p = float(os.getenv("LLM_TOP_P", "0.95"))
        top_k = int(os.getenv("LLM_TOP_K", "50"))
        
        # 重试配置
        retry_config = RetryConfig(
            max_retries=int(os.getenv("LLM_RETRY_MAX", "3")),
            initial_delay_sec=float(os.getenv("LLM_RETRY_INITIAL_DELAY", "1.0")),
            max_delay_sec=float(os.getenv("LLM_RETRY_MAX_DELAY", "30.0")),
            backoff_multiplier=float(os.getenv("LLM_RETRY_BACKOFF", "2.0")),
        )
        
        # 熔断器配置
        circuit_breaker_config = CircuitBreakerConfig(
            enabled=os.getenv("LLM_CIRCUIT_BREAKER_ENABLED", "true").lower() == "true",
            failure_threshold=int(os.getenv("LLM_CIRCUIT_BREAKER_THRESHOLD", "5")),
            success_threshold=int(os.getenv("LLM_CIRCUIT_BREAKER_SUCCESS", "2")),
            timeout_sec=float(os.getenv("LLM_CIRCUIT_BREAKER_TIMEOUT", "60.0")),
        )
        
        # 负载均衡配置
        load_balancer_config = LoadBalancerConfig(
            enabled=os.getenv("LLM_LOAD_BALANCER_ENABLED", "false").lower() == "true",
            strategy=os.getenv("LLM_LOAD_BALANCER_STRATEGY", "round_robin"),
        )
        
        return cls(
            provider=provider,
            environment=environment,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            timeout_sec=timeout_sec,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            retry_config=retry_config,
            circuit_breaker_config=circuit_breaker_config,
            load_balancer_config=load_balancer_config,
            enable_logging=os.getenv("LLM_ENABLE_LOGGING", "true").lower() == "true",
            enable_metrics=os.getenv("LLM_ENABLE_METRICS", "true").lower() == "true",
            log_level=os.getenv("LLM_LOG_LEVEL", "INFO"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "provider": self.provider.value,
            "environment": self.environment.value,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "timeout_sec": self.timeout_sec,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
        }
