"""Sina Finance Stock provider wrapper for provider chain."""

from __future__ import annotations

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider
from infra.tool_clients.providers.sina_finance_provider import (
    SinaFinanceProvider,
    normalize_to_sina_symbol,
    format_stock_display,
)


class SinaStockProvider(ToolProvider):
    """Sina Finance Stock provider wrapper.
    
    Wraps SinaFinanceProvider.get_stock_quote() for provider chain integration.
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.sina_finance = SinaFinanceProvider(timeout=config.timeout)
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute stock quote query via Sina Finance.
        
        Args:
            query: Stock symbol or name (e.g., "上证指数", "600519", "贵州茅台")
            
        Returns:
            ProviderResult with stock quote data
        """
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
            )
        
        # Normalize to Sina symbol format
        symbol = normalize_to_sina_symbol(query)
        
        if not symbol:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_symbol",
            )
        
        # Call Sina Finance API
        result = self.sina_finance.get_stock_quote(symbol)
        
        if not result.success:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=result.error or "unknown_error",
            )
        
        # Format display text
        quote_data = result.data["quote"]
        text = format_stock_display(quote_data, symbol, query)
        
        tool_result = ToolResult(
            ok=True,
            text=text,
            raw={
                "provider": "sina_finance",
                "symbol": symbol,
                "quote": quote_data,
            },
        )
        
        return ProviderResult(
            ok=True,
            data=tool_result,
            provider_name=self.config.name,
            result_type=ResultType.RAW,
        )
    
    def health_check(self) -> bool:
        """Check if Sina Finance API is available.
        
        Returns:
            True (Sina Finance API doesn't require API key)
        """
        return True
