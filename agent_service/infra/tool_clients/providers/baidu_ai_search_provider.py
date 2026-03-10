"""Baidu AI Search provider using Qianfan API."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduAISearchProvider(ToolProvider):
    """Baidu AI Search provider using Qianfan /v2/ai_search API.
    
    This provider uses the OpenAI SDK to call Baidu's AI Search endpoint,
    which returns AI-summarized search results with references.
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("BAIDU_QIANFAN_API_KEY", "").strip()
        self.base_url = "https://qianfan.baidubce.com/v2/ai_search"
        self.model = os.getenv("BAIDU_AI_SEARCH_MODEL", "ernie-3.5-8k")
        self.timeout = config.timeout
        
        # Initialize OpenAI client
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        else:
            self.client = None
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute AI search via Baidu Qianfan.
        
        Args:
            query: Search query string
            
        Returns:
            ProviderResult with AI-summarized content and references
        """
        if not self.client:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_api_key_missing",
            )
        
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
            )
        
        try:
            # Call Baidu AI Search using OpenAI SDK
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": query}],
                stream=False,
            )
            
            # Check for rate limit or other errors
            if hasattr(response, 'code') and response.code:
                error_code = response.code
                error_msg = getattr(response, 'message', 'Unknown error')
                
                # Handle rate limiting
                if 'rate_limit' in error_code:
                    return ProviderResult(
                        ok=False,
                        data=None,
                        provider_name=self.config.name,
                        error=f"rate_limit:{error_msg}",
                    )
                
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error=f"{error_code}:{error_msg}",
                )
            
            # Extract AI summary
            if not response.choices or not response.choices[0].message:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="empty_response",
                )
            
            content = response.choices[0].message.content
            if not content:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="empty_content",
                )
            
            # Format result
            result = ToolResult(
                ok=True,
                text=content,
                raw={
                    "provider": "baidu_ai_search",
                    "query": query,
                    "model": self.model,
                    "response": response.model_dump() if hasattr(response, 'model_dump') else {},
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.SUMMARIZED,  # AI-processed content
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific error types
            if "rate_limit" in error_msg.lower():
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error=f"rate_limit:{error_msg}",
                )
            
            if "timeout" in error_msg.lower():
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error=f"timeout:{error_msg}",
                )
            
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"baidu_error:{error_msg}",
            )
    
    def health_check(self) -> bool:
        """Check if Baidu API key is available.
        
        Returns:
            True if API key is configured, False otherwise
        """
        return bool(self.api_key and self.client)
