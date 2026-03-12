"""推理源管理器 - 支持动态切换和故障转移"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, Any

from infra.llm_clients.llm_config import (
    LLMServiceConfig,
    LLMProvider,
    Environment,
)
from infra.llm_clients.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class InferenceSourceConfig:
    """推理源配置"""
    
    def __init__(
        self,
        name: str,
        provider: LLMProvider,
        base_url: str,
        model_name: str,
        priority: int = 0,
        enabled: bool = True,
        api_key: Optional[str] = None,
        **kwargs
    ):
        self.name = name
        self.provider = provider
        self.base_url = base_url
        self.model_name = model_name
        self.priority = priority
        self.enabled = enabled
        self.api_key = api_key
        self.extra_params = kwargs
    
    def to_config(self, environment: Environment) -> LLMServiceConfig:
        """转换为LLMServiceConfig"""
        return LLMServiceConfig(
            provider=self.provider,
            environment=environment,
            base_url=self.base_url,
            model_name=self.model_name,
            api_key=self.api_key,
            **self.extra_params
        )


class InferenceSourceManager:
    """推理源管理器 - 支持多源管理和动态切换"""
    
    def __init__(self):
        self.sources: Dict[str, InferenceSourceConfig] = {}
        self.current_source: Optional[str] = None
        self.manager: Optional[LLMManager] = None
        self.environment = Environment(os.getenv("LLM_ENVIRONMENT", "dev"))
        self._load_sources_from_env()
    
    def _load_sources_from_env(self) -> None:
        """从环境变量加载推理源配置"""
        # 加载默认推理源
        default_provider = os.getenv("LLM_PROVIDER", "lm_studio")
        default_base_url = os.getenv("LLM_BASE_URL", "http://localhost:1234")
        default_model = os.getenv("LLM_MODEL_NAME", "qwen2.5-7b-instruct-mlx")
        
        try:
            provider = LLMProvider(default_provider)
        except ValueError:
            logger.warning(f"Invalid provider: {default_provider}, using lm_studio")
            provider = LLMProvider.LM_STUDIO
        
        # 注册默认推理源
        self.register_source(
            name="default",
            provider=provider,
            base_url=default_base_url,
            model_name=default_model,
            priority=100,
        )
        
        # 加载其他推理源（如果配置了）
        self._load_additional_sources()
        
        # 设置当前推理源
        self.current_source = "default"
    
    def _load_additional_sources(self) -> None:
        """加载额外的推理源配置"""
        # 从环境变量加载多个推理源
        # 格式: LLM_SOURCES_JSON='{"vllm": {...}, "ollama": {...}}'
        import json
        
        sources_json = os.getenv("LLM_SOURCES_JSON")
        if sources_json:
            try:
                sources_config = json.loads(sources_json)
                for name, config in sources_config.items():
                    self.register_source(
                        name=name,
                        provider=LLMProvider(config.get("provider", "lm_studio")),
                        base_url=config.get("base_url"),
                        model_name=config.get("model_name"),
                        priority=config.get("priority", 0),
                        enabled=config.get("enabled", True),
                        api_key=config.get("api_key"),
                        **config.get("extra_params", {})
                    )
            except Exception as e:
                logger.error(f"Failed to load additional sources: {e}")
    
    def register_source(
        self,
        name: str,
        provider: LLMProvider,
        base_url: str,
        model_name: str,
        priority: int = 0,
        enabled: bool = True,
        api_key: Optional[str] = None,
        **kwargs
    ) -> None:
        """注册推理源"""
        source = InferenceSourceConfig(
            name=name,
            provider=provider,
            base_url=base_url,
            model_name=model_name,
            priority=priority,
            enabled=enabled,
            api_key=api_key,
            **kwargs
        )
        self.sources[name] = source
        logger.info(f"Registered inference source: {name} ({provider.value})")
    
    def switch_source(self, source_name: str) -> bool:
        """切换推理源"""
        if source_name not in self.sources:
            logger.error(f"Source not found: {source_name}")
            return False
        
        source = self.sources[source_name]
        if not source.enabled:
            logger.error(f"Source is disabled: {source_name}")
            return False
        
        try:
            config = source.to_config(self.environment)
            self.manager = LLMManager(config)
            self.current_source = source_name
            logger.info(f"Switched to inference source: {source_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to source {source_name}: {e}")
            return False
    
    def get_current_source(self) -> Optional[str]:
        """获取当前推理源"""
        return self.current_source
    
    def get_source_info(self, source_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取推理源信息"""
        name = source_name or self.current_source
        if not name or name not in self.sources:
            return None
        
        source = self.sources[name]
        return {
            "name": source.name,
            "provider": source.provider.value,
            "base_url": source.base_url,
            "model_name": source.model_name,
            "priority": source.priority,
            "enabled": source.enabled,
        }
    
    def list_sources(self) -> List[Dict[str, Any]]:
        """列出所有推理源"""
        return [
            {
                "name": source.name,
                "provider": source.provider.value,
                "base_url": source.base_url,
                "model_name": source.model_name,
                "priority": source.priority,
                "enabled": source.enabled,
                "current": source.name == self.current_source,
            }
            for source in sorted(
                self.sources.values(),
                key=lambda x: x.priority,
                reverse=True
            )
        ]
    
    def generate(self, user_query: str, system_prompt: str) -> str:
        """使用当前推理源生成文本"""
        if not self.manager:
            if not self.current_source or not self.switch_source(self.current_source):
                raise RuntimeError("No valid inference source available")
        
        return self.manager.generate(user_query, system_prompt)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前推理源的指标"""
        if not self.manager:
            return {}
        
        metrics = self.manager.get_metrics()
        metrics["source"] = self.current_source
        return metrics
    
    def get_circuit_breaker_state(self) -> str:
        """获取熔断器状态"""
        if not self.manager:
            return "unknown"
        return self.manager.get_circuit_breaker_state()
    
    def enable_source(self, source_name: str) -> bool:
        """启用推理源"""
        if source_name not in self.sources:
            return False
        self.sources[source_name].enabled = True
        logger.info(f"Enabled inference source: {source_name}")
        return True
    
    def disable_source(self, source_name: str) -> bool:
        """禁用推理源"""
        if source_name not in self.sources:
            return False
        self.sources[source_name].enabled = False
        logger.info(f"Disabled inference source: {source_name}")
        return True
    
    def failover_to_next(self) -> bool:
        """故障转移到下一个推理源"""
        enabled_sources = [
            s for s in self.sources.values()
            if s.enabled and s.name != self.current_source
        ]
        
        if not enabled_sources:
            logger.error("No available sources for failover")
            return False
        
        # 按优先级排序
        enabled_sources.sort(key=lambda x: x.priority, reverse=True)
        next_source = enabled_sources[0]
        
        logger.warning(f"Failing over from {self.current_source} to {next_source.name}")
        return self.switch_source(next_source.name)


# 全局推理源管理器实例
_inference_source_manager: Optional[InferenceSourceManager] = None


def get_inference_source_manager() -> InferenceSourceManager:
    """获取全局推理源管理器"""
    global _inference_source_manager
    if _inference_source_manager is None:
        _inference_source_manager = InferenceSourceManager()
    return _inference_source_manager


def reset_inference_source_manager() -> None:
    """重置全局推理源管理器（用于测试）"""
    global _inference_source_manager
    _inference_source_manager = None
