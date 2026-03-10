"""Amap MCP provider for find_nearby."""

from __future__ import annotations

from typing import Any

from domain.tools.types import ToolResult
from infra.tool_clients.amap_mcp_client import AmapMCPClient
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult


class AmapMCPProvider:
    """Provider for Amap MCP."""
    
    def __init__(self, config: ProviderConfig | None = None, **kwargs: Any) -> None:
        self.config = config
        self.client = AmapMCPClient()
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.config is None or self.config.enabled
    
    def record_success(self, latency_ms: float) -> None:
        """Record successful execution."""
        pass
    
    def record_failure(self, error_type: str) -> None:
        """Record failed execution."""
        pass
    
    def record_fallback(self) -> None:
        """Record fallback to next provider."""
        pass
    
    def execute(self, **kwargs: Any) -> ProviderResult:
        """Execute find_nearby using Amap MCP.
        
        Args:
            keyword: Search keyword
            city: City name (optional)
            location: Location coordinates (optional)
        
        Returns:
            ProviderResult with tool result
        """
        keyword = kwargs.get("keyword", "")
        city = kwargs.get("city")
        location = kwargs.get("location")
        
        if not keyword:
            return ProviderResult(
                ok=False,
                data=None,
                error="missing_keyword",
                provider_name="amap_mcp",
            )
        
        try:
            result = self.client.find_nearby(keyword=keyword, city=city, location=location)
            
            if result.ok:
                return ProviderResult(
                    ok=True,
                    data=result,
                    error=None,
                    provider_name="amap_mcp",
                )
            else:
                return ProviderResult(
                    ok=False,
                    data=None,
                    error=result.error or "amap_mcp_failed",
                    provider_name="amap_mcp",
                )
        
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                error=f"amap_mcp_exception:{e}",
                provider_name="amap_mcp",
            )
