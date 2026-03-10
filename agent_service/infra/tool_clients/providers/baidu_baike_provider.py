"""Baidu Baike (Encyclopedia) provider."""

import os
import requests
from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduBaikeProvider(ToolProvider):
    """Baidu Baike (Encyclopedia) provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.access_key = os.getenv("BAIDU_BCE_ACCESS_KEY", "").strip()
        self.timeout = config.timeout
        self.base_url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute Baidu Baike query."""
        if not self.access_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_access_key_missing",
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
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_key}",
        }
        
        payload = {
            "app_id": "baidu_baike",
            "query": query,
            "stream": False,
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
            
            # Extract encyclopedia content
            result_data = data.get("result", {})
            summary = result_data.get("summary", "")
            
            if not summary:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_content",
                    result_type=ResultType.SUMMARIZED,
                )
            
            # Extract reference URL
            url = result_data.get("url", "")
            
            # Create result
            result = ToolResult(
                ok=True,
                text=summary,  # Encyclopedia summary, direct use
                raw={
                    "provider": "baidu_baike",
                    "query": query,
                    "summary": summary,
                    "url": url,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.SUMMARIZED,  # Encyclopedia content, direct use
            )
            
        except requests.exceptions.Timeout:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="timeout",
                result_type=ResultType.SUMMARIZED,
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
                result_type=ResultType.SUMMARIZED,
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"error:{e}",
                result_type=ResultType.SUMMARIZED,
            )
    
    def health_check(self) -> bool:
        """Check if access key is available."""
        return bool(self.access_key)
