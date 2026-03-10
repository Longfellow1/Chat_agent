"""Provider chain manager for automatic fallback."""

from __future__ import annotations

import time
from typing import Any, Type

from infra.tool_clients.provider_base import (
    ProviderConfig,
    ProviderMetrics,
    ProviderResult,
    ToolProvider,
)


class ProviderChainManager:
    """Manages provider chains with automatic fallback."""
    
    def __init__(self):
        self._chains: dict[str, list[ToolProvider]] = {}
        self._provider_registry: dict[str, Type[ToolProvider]] = {}
    
    def register_provider(self, name: str, provider_class: Type[ToolProvider]) -> None:
        """Register a provider class.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        self._provider_registry[name] = provider_class
    
    def configure_chain(
        self,
        tool_name: str,
        chain_config: list[ProviderConfig],
    ) -> None:
        """Configure provider chain for a tool.
        
        Args:
            tool_name: Tool name
            chain_config: List of provider configs (will be sorted by priority)
        """
        providers = []
        for config in sorted(chain_config, key=lambda x: x.priority):
            # Skip disabled providers
            if not config.enabled:
                continue
                
            if config.name not in self._provider_registry:
                raise ValueError(f"Provider {config.name} not registered")
            
            provider_class = self._provider_registry[config.name]
            provider = provider_class(config)
            providers.append(provider)
        
        self._chains[tool_name] = providers
    
    def execute(self, tool_name: str, **kwargs) -> ProviderResult:
        """Execute tool call with automatic fallback.
        
        Args:
            tool_name: Tool name
            **kwargs: Tool-specific arguments
            
        Returns:
            ProviderResult from first successful provider
        """
        if tool_name not in self._chains:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name="none",
                error=f"No provider chain configured for {tool_name}",
            )
        
        chain = self._chains[tool_name]
        fallback_chain = []
        last_error = None
        
        for provider in chain:
            if not provider.is_available():
                fallback_chain.append(f"{provider.config.name}:unavailable")
                provider.record_fallback()
                continue
            
            try:
                start = time.time()
                result = provider.execute(**kwargs)
                latency_ms = (time.time() - start) * 1000
                result.latency_ms = latency_ms
                
                if result.ok:
                    provider.record_success(latency_ms)
                    result.fallback_chain = fallback_chain if fallback_chain else None
                    return result
                
                # Check if should fallback
                provider.record_failure("error")
                if self._should_fallback(provider.config, result):
                    fallback_chain.append(f"{provider.config.name}:{result.error}")
                    provider.record_fallback()
                    continue
                else:
                    # Don't fallback, return error
                    result.fallback_chain = fallback_chain if fallback_chain else None
                    return result
                    
            except TimeoutError as e:
                last_error = str(e)
                provider.record_failure("timeout")
                if provider.config.fallback_on_timeout:
                    fallback_chain.append(f"{provider.config.name}:timeout")
                    provider.record_fallback()
                    continue
                else:
                    return ProviderResult(
                        ok=False,
                        data=None,
                        provider_name=provider.config.name,
                        error=f"timeout:{last_error}",
                        fallback_chain=fallback_chain if fallback_chain else None,
                    )
            except Exception as e:
                last_error = str(e)
                provider.record_failure("error")
                if provider.config.fallback_on_error:
                    fallback_chain.append(f"{provider.config.name}:error")
                    provider.record_fallback()
                    continue
                else:
                    return ProviderResult(
                        ok=False,
                        data=None,
                        provider_name=provider.config.name,
                        error=f"error:{last_error}",
                        fallback_chain=fallback_chain if fallback_chain else None,
                    )
        
        # All providers failed
        return ProviderResult(
            ok=False,
            data=None,
            provider_name="none",
            error=f"All providers failed: {last_error}",
            fallback_chain=fallback_chain,
        )
    
    def _should_fallback(self, config: ProviderConfig, result: ProviderResult) -> bool:
        """Check if should fallback to next provider.
        
        Args:
            config: Provider config
            result: Execution result
            
        Returns:
            True if should fallback, False otherwise
        """
        if not result.ok:
            if config.fallback_error_codes and result.error:
                return any(code in result.error for code in config.fallback_error_codes)
            return config.fallback_on_error
        return False
    
    def get_metrics(self, tool_name: str, provider_name: str | None = None) -> dict[str, ProviderMetrics]:
        """Get metrics for tool providers.
        
        Args:
            tool_name: Tool name
            provider_name: Optional provider name (if None, returns all)
            
        Returns:
            Dict of provider_name -> ProviderMetrics
        """
        if tool_name not in self._chains:
            return {}
        
        metrics = {}
        for provider in self._chains[tool_name]:
            if provider_name is None or provider.config.name == provider_name:
                metrics[provider.config.name] = provider.get_metrics()
        
        return metrics
    
    def update_provider_config(
        self,
        tool_name: str,
        provider_name: str,
        **updates: Any,
    ) -> None:
        """Update provider configuration at runtime.
        
        Args:
            tool_name: Tool name
            provider_name: Provider name
            **updates: Config fields to update
        """
        if tool_name not in self._chains:
            raise ValueError(f"Tool {tool_name} not configured")
        
        for provider in self._chains[tool_name]:
            if provider.config.name == provider_name:
                for key, value in updates.items():
                    if hasattr(provider.config, key):
                        setattr(provider.config, key, value)
                return
        
        raise ValueError(f"Provider {provider_name} not found in {tool_name} chain")
