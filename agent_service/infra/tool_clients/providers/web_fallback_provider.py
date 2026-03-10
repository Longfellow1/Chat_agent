"""Web search fallback provider for location queries."""

from __future__ import annotations

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ToolProvider


class WebSearchFallbackProvider(ToolProvider):
    """Web search fallback for location queries."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Will use Tavily provider internally
        from infra.tool_clients.providers.tavily_provider import TavilyProvider
        self.tavily = TavilyProvider(config)
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute location query via web search."""
        keyword = kwargs.get("keyword", "")
        city = kwargs.get("city", "")
        
        # Build search query
        query = f"{city} {keyword}" if city else keyword
        
        # Use Tavily
        result = self.tavily.execute(query=query)
        
        if result.ok and result.data:
            # Add fallback marker
            tool_result: ToolResult = result.data
            tool_result.text = f"[location->web_search_fallback] {tool_result.text}"
            result.data = tool_result
        
        return result
    
    def health_check(self) -> bool:
        """Check if Tavily is available."""
        return self.tavily.health_check()
