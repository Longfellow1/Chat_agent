"""LLM客户端工厂 - 支持多种推理框架的统一接口"""

from __future__ import annotations

import logging
from typing import Optional

from infra.llm_clients.base import LLMClient
from infra.llm_clients.llm_config import LLMProvider, LLMServiceConfig
from infra.llm_clients.providers.vllm_provider import VLLMProvider
from infra.llm_clients.providers.ollama_provider import OllamaProvider
from infra.llm_clients.providers.openai_compatible_provider import OpenAICompatibleProvider
from infra.llm_clients.lm_studio_client import LMStudioClient
from infra.llm_clients.coze_client import CozeClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """LLM客户端工厂"""
    
    _instance: Optional[LLMClientFactory] = None
    _client: Optional[LLMClient] = None
    _config: Optional[LLMServiceConfig] = None
    
    def __new__(cls) -> LLMClientFactory:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def create_client(cls, config: Optional[LLMServiceConfig] = None) -> LLMClient:
        """创建LLM客户端
        
        Args:
            config: LLM服务配置，如果为None则从环境变量加载
            
        Returns:
            LLMClient实例
            
        Raises:
            ValueError: 不支持的提供商或配置错误
        """
        if config is None:
            config = LLMServiceConfig.from_env()
        
        factory = cls()
        factory._config = config
        
        logger.info(
            f"Creating LLM client: provider={config.provider.value}, "
            f"environment={config.environment.value}, model={config.model_name}"
        )
        
        if config.provider == LLMProvider.LM_STUDIO:
            factory._client = LMStudioClient()
        elif config.provider == LLMProvider.VLLM:
            factory._client = VLLMProvider(config)
        elif config.provider == LLMProvider.OLLAMA:
            factory._client = OllamaProvider(config)
        elif config.provider == LLMProvider.OPENAI_COMPATIBLE:
            factory._client = OpenAICompatibleProvider(config)
        elif config.provider == LLMProvider.COZE:
            factory._client = CozeClient()
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
        
        return factory._client
    
    @classmethod
    def get_client(cls) -> LLMClient:
        """获取已创建的客户端，如果不存在则创建"""
        factory = cls()
        if factory._client is None:
            factory.create_client()
        return factory._client
    
    @classmethod
    def get_config(cls) -> LLMServiceConfig:
        """获取当前配置"""
        factory = cls()
        if factory._config is None:
            factory._config = LLMServiceConfig.from_env()
        return factory._config
    
    @classmethod
    def reset(cls) -> None:
        """重置工厂（用于测试）"""
        factory = cls()
        factory._client = None
        factory._config = None
