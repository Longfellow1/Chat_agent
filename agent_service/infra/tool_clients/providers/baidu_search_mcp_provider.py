"""Baidu Search MCP provider."""

import os
import requests
from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduSearchMCPProvider(ToolProvider):
    """Baidu Search MCP provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.access_key = os.getenv("BAIDU_BCE_ACCESS_KEY", "").strip()
        self.timeout = config.timeout
        self.base_url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
        self.max_results = int(os.getenv("TOOL_SEARCH_MAX_RESULTS", "5"))
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute Baidu Search via MCP."""
        if not self.access_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_access_key_missing",
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
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_key}",
        }
        
        payload = {
            "app_id": "mcp_baidu_web_search",
            "query": query,
            "stream": False,
            "tools": [
                {
                    "type": "baidu_search",
                    "baidu_search": {
                        "top_n": self.max_results
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract search results
            result_data = data.get("result", {})
            search_results = result_data.get("search_results", [])
            
            if not search_results:
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
                search_results,
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
                    "provider": "baidu_search_mcp",
                    "query": query,
                    "results": processed,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.RAW,  # Raw results, needs processing
            )
            
        except requests.exceptions.Timeout:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="timeout",
                result_type=ResultType.RAW,
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"http_error:{e.response.status_code}"
            if e.response.status_code == 429:
                error_msg = "rate_limit"
            elif e.response.status_code == 403:
                error_msg = "quota_exceeded"
            
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=error_msg,
                result_type=ResultType.RAW,
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"error:{e}",
                result_type=ResultType.RAW,
            )
    
    def health_check(self) -> bool:
        """Check if access key is available."""
        return bool(self.access_key)
