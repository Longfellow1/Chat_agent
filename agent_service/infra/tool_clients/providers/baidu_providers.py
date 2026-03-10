"""Baidu search providers (traditional API and AI search)."""

from __future__ import annotations

import json
import os
import urllib.request

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduSearchProvider(ToolProvider):
    """Baidu traditional search provider (Bing-like raw results)."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("BAIDU_SEARCH_API_KEY", "").strip()
        self.timeout = config.timeout
        self.max_results = int(os.getenv("TOOL_SEARCH_MAX_RESULTS", "3"))
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute web search via Baidu traditional API."""
        if not self.api_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_api_key_missing",
                result_type=ResultType.RAW,
            )
        
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
                result_type=ResultType.RAW,
            )
        
        # Baidu Search API endpoint (example)
        url = "https://api.baidu.com/search/v1"
        payload = {
            "query": query,
            "max_results": self.max_results,
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "agent-service/0.1",
                },
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            
            results = body.get("results") or []
            if not results:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_results",
                    result_type=ResultType.RAW,
                )
            
            # Process results using search_result_processor
            from infra.tool_clients.search_result_processor import process_search_results
            processed = process_search_results(
                results,
                query=query,
                max_results=self.max_results,
                relevance_threshold=0.3,
            )
            
            if not processed:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_relevant_results",
                    result_type=ResultType.RAW,
                )
            
            # Format output
            lines = []
            for i, r in enumerate(processed, 1):
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("snippet", "")[:80]
                credibility = r.get("credibility", 5)
                
                trust_mark = ""
                if credibility >= 9:
                    trust_mark = " [官方]"
                elif credibility >= 7:
                    trust_mark = " [可信]"
                
                lines.append(f"{i}. {title}{trust_mark} | {url} | {snippet}")
            
            text = f"已搜索{query}，结果如下：\n" + "\n".join(lines)
            
            result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "baidu_search",
                    "query": query,
                    "results": processed,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.RAW,  # Raw results, processed
            )
            
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"baidu_search_error:{e}",
                result_type=ResultType.RAW,
            )
    
    def health_check(self) -> bool:
        """Check if Baidu API key is available."""
        return bool(self.api_key)


class BaiduAISearchProvider(ToolProvider):
    """Baidu Qianfan AI Search provider using /v2/ai_search API.
    
    Uses OpenAI SDK to call Baidu's AI Search endpoint which returns
    AI-summarized search results with references.
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("BAIDU_QIANFAN_API_KEY", "").strip()
        self.base_url = "https://qianfan.baidubce.com/v2/ai_search"
        self.model = os.getenv("BAIDU_AI_SEARCH_MODEL", "ernie-3.5-8k")
        self.timeout = config.timeout
        
        # Initialize OpenAI client
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout,
                )
            except ImportError:
                self.client = None
        else:
            self.client = None
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute AI search via Baidu Qianfan.
        
        Args:
            query: Search query string
            
        Returns:
            ProviderResult with AI-summarized content
        """
        if not self.client:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_api_key_missing_or_openai_not_installed",
                result_type=ResultType.SUMMARIZED,
            )
        
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
                result_type=ResultType.SUMMARIZED,
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
                        result_type=ResultType.SUMMARIZED,
                    )
                
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error=f"{error_code}:{error_msg}",
                    result_type=ResultType.SUMMARIZED,
                )
            
            # Extract AI summary
            if not response.choices or not response.choices[0].message:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="empty_response",
                    result_type=ResultType.SUMMARIZED,
                )
            
            content = response.choices[0].message.content
            if not content:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="empty_content",
                    result_type=ResultType.SUMMARIZED,
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
                    result_type=ResultType.SUMMARIZED,
                )
            
            if "timeout" in error_msg.lower():
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error=f"timeout:{error_msg}",
                    result_type=ResultType.SUMMARIZED,
                )
            
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"baidu_error:{error_msg}",
                result_type=ResultType.SUMMARIZED,
            )
    
    def health_check(self) -> bool:
        """Check if Baidu API key is available."""
        return bool(self.api_key and self.client)
