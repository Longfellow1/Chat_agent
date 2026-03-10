"""Tavily web search provider."""

from __future__ import annotations

import json
import os
import urllib.request

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class TavilyProvider(ToolProvider):
    """Tavily web search provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.timeout = config.timeout
        self.max_results = int(os.getenv("TOOL_SEARCH_MAX_RESULTS", "3"))
        self.snippet_chars = int(os.getenv("TOOL_SEARCH_SNIPPET_CHARS", "200"))  # 更保守的截断策略，确保 LLM 有充分上下文
        self.search_depth = os.getenv("TOOL_SEARCH_DEPTH", "basic").strip().lower()
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute web search via Tavily."""
        if not self.api_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="tavily_api_key_missing",
            )
        
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
            )
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": self.search_depth,
            "topic": "general",
            "max_results": max(1, self.max_results * 2),
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=data,
                headers={
                    "Content-Type": "application/json",
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
                )
            
            # Process results
            from infra.tool_clients.search_result_processor import process_search_results
            processed = process_search_results(
                results,
                query=query,
                max_results=self.max_results,
                relevance_threshold=0.1,  # 降低阈值从 0.3 到 0.1
            )
            
            if not processed:
                # 保底逻辑：至少返回相关性最高的 1 条
                if results:
                    best = max(results, key=lambda x: x.get('score', 0))
                    processed = [best]
                else:
                    return ProviderResult(
                        ok=False,
                        data=None,
                        provider_name=self.config.name,
                        error="no_relevant_results",
                    )
            
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
            
            result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "tavily",
                    "query": query,
                    "results": processed,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.RAW,  # Tavily returns raw results
            )
            
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"tavily_error:{e}",
            )
    
    def health_check(self) -> bool:
        """Check if Tavily API key is available."""
        return bool(self.api_key)
