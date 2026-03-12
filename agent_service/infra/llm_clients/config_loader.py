"""LLM配置加载器 - 支持JSON、YAML、环境变量"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """从JSON文件加载配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON config from {file_path}: {e}")
            return {}
    
    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """从YAML文件加载配置"""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            logger.warning("PyYAML not installed, skipping YAML config")
            return {}
        except Exception as e:
            logger.error(f"Failed to load YAML config from {file_path}: {e}")
            return {}
    
    @staticmethod
    def load_env_vars(prefix: str = "LLM_") -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config[config_key] = value
        return config
    
    @staticmethod
    def resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的环境变量引用"""
        def resolve_value(value: Any) -> Any:
            if isinstance(value, str):
                # 处理 ${VAR_NAME} 格式
                if value.startswith("${") and value.endswith("}"):
                    var_name = value[2:-1]
                    return os.getenv(var_name, value)
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(v) for v in value]
            return value
        
        return resolve_value(config)
    
    @staticmethod
    def load_config(
        config_file: Optional[str] = None,
        env_prefix: str = "LLM_",
    ) -> Dict[str, Any]:
        """加载配置（支持多种格式）"""
        config = {}
        
        # 1. 从配置文件加载
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                if config_file.endswith('.json'):
                    config = ConfigLoader.load_json(config_file)
                elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    config = ConfigLoader.load_yaml(config_file)
                logger.info(f"Loaded config from {config_file}")
        
        # 2. 从环境变量加载（覆盖文件配置）
        env_config = ConfigLoader.load_env_vars(env_prefix)
        config.update(env_config)
        
        # 3. 解析环境变量引用
        config = ConfigLoader.resolve_env_vars(config)
        
        return config


class LLMSourcesConfigLoader:
    """LLM推理源配置加载器"""
    
    @staticmethod
    def load_sources(
        config_file: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """加载推理源配置"""
        # 默认配置文件路径
        if not config_file:
            config_file = os.getenv(
                "LLM_SOURCES_CONFIG",
                "config/llm_sources.json"
            )
        
        # 加载配置
        config = ConfigLoader.load_json(config_file)
        
        if not config:
            logger.warning(f"No config found in {config_file}")
            return {}
        
        # 过滤环境特定的源
        if environment:
            sources = config.get("sources", {})
            filtered_sources = {}
            for name, source_config in sources.items():
                source_env = source_config.get("environment")
                if not source_env or source_env == environment:
                    filtered_sources[name] = source_config
            config["sources"] = filtered_sources
        
        return config
    
    @staticmethod
    def get_default_source(config: Dict[str, Any]) -> Optional[str]:
        """获取默认推理源"""
        return config.get("default_source")
    
    @staticmethod
    def is_failover_enabled(config: Dict[str, Any]) -> bool:
        """检查是否启用故障转移"""
        return config.get("failover_enabled", True)
    
    @staticmethod
    def get_failover_strategy(config: Dict[str, Any]) -> str:
        """获取故障转移策略"""
        return config.get("failover_strategy", "priority")
