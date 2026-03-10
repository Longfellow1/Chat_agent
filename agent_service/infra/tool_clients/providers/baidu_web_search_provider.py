"""Baidu Web Search provider using AISearch component (returns raw references)."""

from __future__ import annotations

import os

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduWebSearchProvider(ToolProvider):
    """Baidu Web Search provider using appbuilder AISearch component.
    
    Returns raw search results (references list with title/url/content).
    Suitable for local LLM processing.
    
    API Limits:
    - Free quota: 1000 calls/day
    - Rate limit: 3 QPS
    - Cost: ¥0.036/call
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("BAIDU_QIANFAN_API_KEY", "").strip()
        self.timeout = config.timeout
        self.max_results = int(os.getenv("TOOL_SEARCH_MAX_RESULTS", "5"))
        self.snippet_chars = int(os.getenv("TOOL_SEARCH_SNIPPET_CHARS", "200"))  # 更保守的截断策略
        
        # Initialize appbuilder client
        if self.api_key:
            try:
                import appbuilder
                os.environ["APPBUILDER_TOKEN"] = self.api_key
                self.search = appbuilder.AISearch()
                self.appbuilder = appbuilder
            except ImportError:
                self.search = None
                self.appbuilder = None
        else:
            self.search = None
            self.appbuilder = None
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute web search via Baidu AISearch.
        
        Args:
            query: Search query string
            
        Returns:
            ProviderResult with raw search results (references list)
        """
        if not self.search:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_api_key_missing_or_appbuilder_not_installed",
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
            # Call Baidu AISearch
            result = self.search.run(messages=[{"role": "user", "content": query}])
            
            # Extract references
            if not hasattr(result, 'content') or not result.content:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="empty_response",
                )
            
            content = result.content
            if not hasattr(content, 'references') or not content.references:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_references",
                )
            
            # Convert references to standard format
            references = []
            for ref in content.references[:self.max_results]:
                references.append({
                    "title": ref.title or "",
                    "url": ref.url or "",
                    "snippet": ref.content or "",
                    "date": ref.date or "",
                })
            
            if not references:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_results",
                )
            
            # Process results using search_result_processor
            from infra.tool_clients.search_result_processor import process_search_results
            processed = process_search_results(
                references,
                query=query,
                max_results=self.max_results,
                relevance_threshold=0.1,
            )
            
            if not processed:
                # Fallback: return at least top result
                processed = references[:1]
            
            # Format output
            lines = []
            for i, r in enumerate(processed, 1):
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("snippet", "")[:self.snippet_chars]
                credibility = r.get("credibility", 5)
                
                trust_mark = ""
                if credibility >= 9:
                    trust_mark = " [官方]"
                elif credibility >= 7:
                    trust_mark = " [可信]"
                
                lines.append(f"{i}. {title}{trust_mark} | {url} | {snippet}")
            
            text = f"已搜索{query}，结果如下：\n" + "\n".join(lines)
            
            tool_result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "baidu_web_search",
                    "query": query,
                    "results": processed,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=tool_result,
                provider_name=self.config.name,
                result_type=ResultType.RAW,  # Raw results for local processing
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific error types
            if "rate" in error_msg.lower() or "qps" in error_msg.lower():
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
        return bool(self.api_key and self.search)
