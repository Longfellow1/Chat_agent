"""Sina News provider for financial and general news."""

from __future__ import annotations

import os
import urllib.parse

import requests

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class SinaNewsProvider(ToolProvider):
    """Sina News provider for financial news.
    
    Returns raw news results from Sina Finance API.
    Optimized for financial and business news.
    
    API: Free, no authentication required
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.timeout = config.timeout
        self.max_results = int(os.getenv("TOOL_NEWS_MAX_RESULTS", "5"))
        self.snippet_chars = int(os.getenv("TOOL_NEWS_SNIPPET_CHARS", "200"))
        self.headers = {"Referer": "https://finance.sina.com.cn"}
        
        # News categories
        self.categories = {
            "finance": "2509",  # 财经滚动
            "stock": "2510",    # 股票
            "fund": "2511",     # 基金
            "futures": "2512",  # 期货
            "forex": "2513",    # 外汇
        }
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute news search via Sina Finance API.
        
        Args:
            query: News query string
            category: News category (finance/stock/fund/futures/forex)
            
        Returns:
            ProviderResult with raw news results
        """
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
            )
        
        # Determine category from query
        category = self._detect_category(query)
        category_id = self.categories.get(category, "2509")
        
        url = "https://feed.mix.sina.com.cn/api/roll/get?" + urllib.parse.urlencode({
            "pageid": "153",
            "lid": category_id,
            "num": str(self.max_results),
            "page": "1",
        })
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("result", {}).get("status", {}).get("code") != 0:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="api_error",
                )
            
            result_data = data.get("result", {})
            news_items = result_data.get("data", [])
            
            if not news_items:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_results",
                )
            
            # Convert to standard format
            references = []
            for item in news_items:
                references.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("intro", ""),
                    "published_date": item.get("ctime", ""),
                    "source": "新浪财经",
                })
            
            # Format output
            lines = []
            for i, r in enumerate(references, 1):
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("snippet", "")[:self.snippet_chars]
                date = r.get("published_date", "")
                
                date_str = f" ({date})" if date else ""
                
                lines.append(f"{i}. {title}{date_str}\n   {url}\n   {snippet}")
            
            text = f"已搜索新闻：{query}\n\n" + "\n\n".join(lines)
            
            tool_result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "sina_news",
                    "query": query,
                    "category": category,
                    "results": references,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=tool_result,
                provider_name=self.config.name,
                result_type=ResultType.RAW,
            )
            
        except requests.Timeout:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="timeout",
            )
        except requests.RequestException as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"request_failed:{str(e)}",
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"sina_error:{str(e)}",
            )
    
    def health_check(self) -> bool:
        """Check if Sina API is accessible.
        
        Returns:
            True if accessible, False otherwise
        """
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=1&page=1"
            response = requests.get(url, headers=self.headers, timeout=3.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def _detect_category(self, query: str) -> str:
        """Detect news category from query.
        
        Args:
            query: Query string
            
        Returns:
            Category name
        """
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["股票", "股市", "a股", "港股", "美股", "涨跌"]):
            return "stock"
        elif any(kw in query_lower for kw in ["基金", "etf"]):
            return "fund"
        elif any(kw in query_lower for kw in ["期货", "商品"]):
            return "futures"
        elif any(kw in query_lower for kw in ["外汇", "汇率", "美元", "人民币"]):
            return "forex"
        else:
            return "finance"
