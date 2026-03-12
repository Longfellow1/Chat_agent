"""Provider configuration loader."""

from __future__ import annotations

import os
from typing import Any

from infra.tool_clients.provider_base import ProviderConfig


def load_provider_configs() -> dict[str, list[ProviderConfig]]:
    """Load provider configurations for all tools.
    
    Returns:
        Dict of tool_name -> list of ProviderConfig
    """
    # Default configurations
    configs = {
        "find_nearby": [
            ProviderConfig(
                name="amap_mcp",
                priority=1,
                timeout=float(os.getenv("AMAP_MCP_TIMEOUT", "3.0")),
                max_retries=2,
                enabled=_is_enabled("AMAP_MCP_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["no_results", "no_poi_results", "api_limit"],
            ),
            ProviderConfig(
                name="baidu_maps_mcp",
                priority=2,
                timeout=float(os.getenv("BAIDU_MAPS_MCP_TIMEOUT", "3.0")),
                max_retries=2,
                enabled=_is_enabled("BAIDU_MAPS_MCP_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["no_results", "no_poi_results", "api_limit"],
            ),
        ],
        "get_weather": [
            ProviderConfig(
                name="qweather",
                priority=1,
                timeout=float(os.getenv("QWEATHER_TIMEOUT", "3.0")),
                max_retries=2,
                enabled=_is_enabled("QWEATHER_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["city_not_found", "api_limit", "timeout"],
            ),
            ProviderConfig(
                name="tavily",
                priority=2,
                timeout=float(os.getenv("TAVILY_TIMEOUT", "3.0")),
                max_retries=1,
                enabled=_is_enabled("TAVILY_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
            ),
        ],
        "web_search": [
            ProviderConfig(
                name="baidu_web_search",
                priority=1,
                timeout=float(os.getenv("BAIDU_WEB_SEARCH_TIMEOUT", "10.0")),
                max_retries=2,
                enabled=_is_enabled("BAIDU_WEB_SEARCH_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["no_results", "no_relevant_results", "rate_limit", "qps", "timeout"],
            ),
            ProviderConfig(
                name="bing_mcp",
                priority=2,
                timeout=float(os.getenv("BING_MCP_TIMEOUT", "8.0")),
                max_retries=2,
                enabled=False,  # 禁用Bing MCP，使用百度搜索
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["no_results", "no_relevant_results", "timeout"],
            ),
            ProviderConfig(
                name="tavily",
                priority=3,
                timeout=float(os.getenv("TAVILY_TIMEOUT", "5.0")),
                max_retries=1,
                enabled=_is_enabled("TAVILY_ENABLED", True),
                fallback_on_timeout=False,
                fallback_on_error=False,
            ),
        ],
        "encyclopedia": [
            ProviderConfig(
                name="baidu_baike",
                priority=1,
                timeout=float(os.getenv("BAIDU_BAIKE_TIMEOUT", "2.5")),
                max_retries=1,
                enabled=_is_enabled("BAIDU_BAIKE_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["no_content", "rate_limit", "quota_exceeded"],
            ),
            ProviderConfig(
                name="baidu_search_mcp",
                priority=2,
                timeout=float(os.getenv("BAIDU_SEARCH_MCP_TIMEOUT", "3.0")),
                max_retries=1,
                enabled=_is_enabled("BAIDU_SEARCH_MCP_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["no_results", "rate_limit", "quota_exceeded"],
            ),
            ProviderConfig(
                name="tavily",
                priority=3,
                timeout=float(os.getenv("TAVILY_TIMEOUT", "3.0")),
                max_retries=1,
                enabled=_is_enabled("TAVILY_ENABLED", True),
                fallback_on_timeout=False,
                fallback_on_error=False,
            ),
        ],
        "get_news": [
            ProviderConfig(
                name="sina_news",
                priority=1,
                timeout=float(os.getenv("SINA_NEWS_TIMEOUT", "3.0")),
                max_retries=2,
                enabled=_is_enabled("SINA_NEWS_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["no_results", "timeout", "api_error"],
            ),
        ],
        "get_news_general": [
            ProviderConfig(
                name="baidu_web_search",
                priority=1,
                timeout=float(os.getenv("BAIDU_WEB_SEARCH_TIMEOUT", "5.0")),
                max_retries=2,
                enabled=_is_enabled("BAIDU_WEB_SEARCH_ENABLED", True),
                fallback_on_timeout=False,
                fallback_on_error=False,
            ),
        ],
        "get_stock": [
            ProviderConfig(
                name="sina_finance",
                priority=1,
                timeout=float(os.getenv("SINA_FINANCE_TIMEOUT", "3.0")),
                max_retries=2,
                enabled=_is_enabled("SINA_FINANCE_ENABLED", True),
                fallback_on_timeout=True,
                fallback_on_error=True,
                fallback_error_codes=["missing_symbol", "access_denied", "parse_error", "invalid_data", "timeout"],
            ),
        ],
    }
    
    return configs


def _is_enabled(env_var: str, default: bool) -> bool:
    """Check if provider is enabled via environment variable.
    
    Args:
        env_var: Environment variable name
        default: Default value if not set
        
    Returns:
        True if enabled, False otherwise
    """
    value = os.getenv(env_var, "").strip().lower()
    if not value:
        return default
    return value in ("true", "1", "yes", "on")


def update_config_from_env(config: ProviderConfig) -> ProviderConfig:
    """Update provider config from environment variables.
    
    Args:
        config: Provider config
        
    Returns:
        Updated config
    """
    prefix = f"{config.name.upper()}_"
    
    # Check for timeout override
    timeout_var = f"{prefix}TIMEOUT"
    if timeout_var in os.environ:
        try:
            config.timeout = float(os.environ[timeout_var])
        except ValueError:
            pass
    
    # Check for enabled override
    enabled_var = f"{prefix}ENABLED"
    if enabled_var in os.environ:
        config.enabled = _is_enabled(enabled_var, config.enabled)
    
    return config
