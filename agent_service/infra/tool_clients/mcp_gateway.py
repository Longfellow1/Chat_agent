"""Unified MCP-style tool gateway.

All external tools are accessed through one `invoke` entrypoint.
If API keys/providers are unavailable, it falls back to LLM-generated responses.

For Amap: Uses MCP server instead of direct API calls.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import gzip
import re
from typing import Any

from domain.tools.types import ToolResult
from infra.tool_clients.providers.sina_finance_provider import (
    SinaFinanceProvider,
    normalize_to_sina_symbol,
    format_stock_display,
)
from infra.tool_clients.amap_mcp_client import AmapMCPClient


class MCPToolGateway:
    """Unified MCP-style tool gateway.

    All external tools are accessed through one `invoke` entrypoint.
    If API keys/providers are unavailable, it falls back to LLM-generated responses.
    """

    def __init__(self) -> None:
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
        self.tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.qweather_key = os.getenv("QWEATHER_API_KEY", "").strip()
        self.qweather_host = os.getenv("QWEATHER_API_HOST", "").strip()
        self.amap_key = os.getenv("AMAP_API_KEY", "").strip()
        self.timeout = float(os.getenv("TOOL_HTTP_TIMEOUT_SEC", "8"))
        self.search_max_results = int(os.getenv("TOOL_SEARCH_MAX_RESULTS", "3"))
        self.search_snippet_chars = int(os.getenv("TOOL_SEARCH_SNIPPET_CHARS", "80"))
        self.search_depth = os.getenv("TOOL_SEARCH_DEPTH", "basic").strip().lower()
        
        # 初始化新浪财经provider
        self.sina_finance = SinaFinanceProvider(timeout=self.timeout)
        self.news_depth = os.getenv("TOOL_NEWS_DEPTH", "basic").strip().lower()
        self.trip_depth = os.getenv("TOOL_TRIP_DEPTH", "basic").strip().lower()
        self.enable_network_fallback = os.getenv("ENABLE_NETWORK_FALLBACK", "true").strip().lower() == "true"
        
        # 超时降级配置（放缓，避免过于激进）
        self.tavily_timeout = float(os.getenv("TAVILY_TIMEOUT_SEC", "3.0"))  # 3秒，避免过于激进
        self.llm_timeout = float(os.getenv("LLM_TIMEOUT_SEC", "5.0"))  # 5秒，避免过于激进
        self.enable_timeout_fallback = os.getenv("ENABLE_TIMEOUT_FALLBACK", "true").strip().lower() == "true"
        
        # Initialize Amap MCP client
        self.amap_mcp: AmapMCPClient | None = None
        if self.amap_key:
            try:
                self.amap_mcp = AmapMCPClient()
            except Exception as e:
                import sys
                print(f"Warning: Failed to initialize Amap MCP client: {e}", file=sys.stderr)
        
        # Initialize web_search provider chain
        self._init_web_search_chain()
        
        # Initialize get_news provider chain
        self._init_get_news_chain()
        
        # Initialize get_stock provider chain
        self._init_get_stock_chain()
        
        # Initialize find_nearby provider chain
        self._init_find_nearby_chain()
        
        # Initialize get_weather provider chain
        self._init_get_weather_chain()
        
        # News deduplication cache: {query: set(title_hashes)}
        self._news_cache: dict[str, set[str]] = {}
    
    def _init_find_nearby_chain(self) -> None:
        """Initialize find_nearby provider chain (Amap MCP -> Baidu Maps MCP -> LLM Fallback)."""
        try:
            from infra.tool_clients.provider_chain import ProviderChainManager
            from infra.tool_clients.provider_config import load_provider_configs
            from infra.tool_clients.providers.amap_mcp_provider import AmapMCPProvider
            from infra.tool_clients.providers.baidu_maps_mcp_provider import BaiduMapsMCPProvider
            
            self.find_nearby_chain = ProviderChainManager()
            
            # Register providers (NO MOCK)
            self.find_nearby_chain.register_provider("amap_mcp", AmapMCPProvider)
            self.find_nearby_chain.register_provider("baidu_maps_mcp", BaiduMapsMCPProvider)
            
            # Load configuration
            configs = load_provider_configs()
            if "find_nearby" in configs:
                self.find_nearby_chain.configure_chain("find_nearby", configs["find_nearby"])
                self.use_find_nearby_chain = True
            else:
                self.use_find_nearby_chain = False
            
        except Exception as e:
            import sys
            print(f"Warning: Failed to initialize find_nearby provider chain: {e}", file=sys.stderr)
            self.find_nearby_chain = None
            self.use_find_nearby_chain = False
    
    def _init_get_weather_chain(self) -> None:
        """Initialize get_weather provider chain (QWeather -> Tavily -> LLM Fallback)."""
        try:
            from infra.tool_clients.provider_chain import ProviderChainManager
            from infra.tool_clients.provider_config import load_provider_configs
            from infra.tool_clients.providers.qweather_provider import QWeatherProvider
            from infra.tool_clients.providers.tavily_provider import TavilyProvider            
            self.get_weather_chain = ProviderChainManager()
            
            # Register providers
            self.get_weather_chain.register_provider("qweather", QWeatherProvider)
            self.get_weather_chain.register_provider("tavily", TavilyProvider)            
            # Load configuration
            configs = load_provider_configs()
            if "get_weather" in configs:
                self.get_weather_chain.configure_chain("get_weather", configs["get_weather"])
                self.use_get_weather_chain = True
            else:
                self.use_get_weather_chain = False
            
        except Exception as e:
            import sys
            print(f"Warning: Failed to initialize get_weather provider chain: {e}", file=sys.stderr)
            self.get_weather_chain = None
            self.use_get_weather_chain = False
    
    def _init_web_search_chain(self) -> None:
        """Initialize web_search provider chain using provider_config."""
        try:
            from infra.tool_clients.provider_chain import ProviderChainManager
            from infra.tool_clients.provider_config import load_provider_configs
            from infra.tool_clients.providers.bing_mcp_provider import BingMCPProvider
            from infra.tool_clients.providers.tavily_provider import TavilyProvider
            from infra.tool_clients.providers.baidu_web_search_provider import BaiduWebSearchProvider
            
            self.web_search_chain = ProviderChainManager()
            
            # Register providers
            self.web_search_chain.register_provider("bing_mcp", BingMCPProvider)
            self.web_search_chain.register_provider("tavily", TavilyProvider)
            self.web_search_chain.register_provider("baidu_web_search", BaiduWebSearchProvider)
            
            # Load config from provider_config.py
            configs = load_provider_configs()
            chain_config = configs.get("web_search", [])
            
            self.web_search_chain.configure_chain("web_search", chain_config)
            self.use_provider_chain = True
            
        except Exception as e:
            import sys
            print(f"Warning: Failed to initialize web_search provider chain: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.web_search_chain = None
            self.use_provider_chain = False
    
    def _init_get_news_chain(self) -> None:
        """Initialize get_news provider chains (finance + general)."""
        try:
            from infra.tool_clients.provider_chain import ProviderChainManager
            from infra.tool_clients.provider_config import load_provider_configs
            from infra.tool_clients.providers.news_provider import SinaNewsProvider
            from infra.tool_clients.providers.baidu_web_search_provider import BaiduWebSearchProvider
            
            # Finance news chain (Sina only)
            self.get_news_finance_chain = ProviderChainManager()
            self.get_news_finance_chain.register_provider("sina_news", SinaNewsProvider)
            
            # General news chain (Baidu Web Search)
            self.get_news_general_chain = ProviderChainManager()
            self.get_news_general_chain.register_provider("baidu_web_search", BaiduWebSearchProvider)
            
            # Load configuration
            configs = load_provider_configs()
            if "get_news" in configs:
                self.get_news_finance_chain.configure_chain("get_news", configs["get_news"])
                self.use_get_news_finance_chain = True
            else:
                self.use_get_news_finance_chain = False
            
            if "get_news_general" in configs:
                self.get_news_general_chain.configure_chain("get_news_general", configs["get_news_general"])
                self.use_get_news_general_chain = True
            else:
                self.use_get_news_general_chain = False
            
        except Exception as e:
            import sys
            print(f"Warning: Failed to initialize get_news provider chains: {e}", file=sys.stderr)
            self.get_news_finance_chain = None
            self.get_news_general_chain = None
            self.use_get_news_finance_chain = False
            self.use_get_news_general_chain = False
    
    def _init_get_stock_chain(self) -> None:
        """Initialize get_stock provider chain (Sina -> Web Search -> LLM Fallback)."""
        try:
            from infra.tool_clients.provider_chain import ProviderChainManager
            from infra.tool_clients.provider_config import load_provider_configs
            from infra.tool_clients.providers.sina_stock_provider import SinaStockProvider            
            self.get_stock_chain = ProviderChainManager()
            
            # Register providers
            self.get_stock_chain.register_provider("sina_finance", SinaStockProvider)            
            # Load configuration
            configs = load_provider_configs()
            if "get_stock" in configs:
                self.get_stock_chain.configure_chain("get_stock", configs["get_stock"])
                self.use_get_stock_chain = True
            else:
                self.use_get_stock_chain = False
            
        except Exception as e:
            import sys
            print(f"Warning: Failed to initialize get_stock provider chain: {e}", file=sys.stderr)
            self.get_stock_chain = None
            self.use_get_stock_chain = False

    def invoke(self, tool_name: str, tool_args: dict[str, Any]) -> ToolResult:
        if tool_name == "get_weather":
            city = str(tool_args.get("city", "")).strip()
            return self._weather(city)
        if tool_name == "get_stock":
            target = str(tool_args.get("target", "")).strip()
            return self._stock(target)
        if tool_name == "web_search":
            query = str(tool_args.get("query", "")).strip()
            return self._web_search(query)
        if tool_name == "get_news":
            topic = str(tool_args.get("topic", "今日热点")).strip()
            return self._news(topic)
        if tool_name == "find_nearby":
            keyword = str(tool_args.get("keyword", "餐厅")).strip()
            city = tool_args.get("city")
            city = str(city).strip() if city else None
            location = tool_args.get("location")
            location = str(location).strip() if location else None
            return self._nearby(keyword=keyword, city=city, location=location)
        if tool_name == "plan_trip":
            destination = str(tool_args.get("destination", "")).strip()
            days = int(tool_args.get("days", 2))
            travel_mode = str(tool_args.get("travel_mode", "transit")).strip()
            return self._trip(destination=destination, days=days, travel_mode=travel_mode)

        return ToolResult(ok=False, text="工具不存在", error="tool_not_found")

    def _weather(self, city: str) -> ToolResult:
        if not city:
            return ToolResult(ok=False, text="缺少城市信息", error="missing_city")
        
        # 1. Try Amap MCP weather (primary)
        if self.amap_mcp:
            try:
                result = self.amap_mcp.get_weather(city)
                if result.ok:
                    return result
                print(f"Amap MCP weather failed: {result.error}, trying QWeather")
            except Exception as e:
                print(f"Amap MCP weather error: {e}, trying QWeather")
        
        # 2. Try QWeather API (secondary, keep for when network is good)
        if self.qweather_key:
            try:
                city_id = self._qweather_lookup_city_id(city)
                if not city_id:
                    raise ValueError(f"City not found: {city}")
                now_data = self._qweather_now(city_id)
                daily_data = self._qweather_3d(city_id)
                now = now_data.get("now", {})
                dailies = daily_data.get("daily") or []
                today = dailies[0] if len(dailies) > 0 else {}
                tomorrow = dailies[1] if len(dailies) > 1 else {}
                text = (
                    f"{city}当前：{now.get('text', '未知')}，{now.get('temp', '-')}°C（体感{now.get('feelsLike', '-')}°C），"
                    f"湿度{now.get('humidity', '-')}%，风{now.get('windDir', '-')}{now.get('windScale', '-') }级。"
                    f"今日预报：{today.get('textDay', '-') }，{today.get('tempMin', '-') }~{today.get('tempMax', '-') }°C；"
                    f"明日预报：{tomorrow.get('textDay', '-') }，{tomorrow.get('tempMin', '-') }~{tomorrow.get('tempMax', '-') }°C。"
                )
                return ToolResult(
                    ok=True,
                    text=text,
                    raw={
                        "provider": "qweather",
                        "city": city,
                        "city_id": city_id,
                        "now": now,
                        "daily_3d": dailies[:3],
                        "update_time": now_data.get("updateTime"),
                        "fx_link": now_data.get("fxLink"),
                    },
                )
            except Exception as e:
                print(f"QWeather failed: {e}, falling back to Tavily")
        
        # 3. Fallback to web_search
        return self._fallback_to_web_search(
            original_tool="get_weather",
            query=f"{city} 天气",
            error="amap_qweather_fail",
            fallback_chain=["amap_mcp", "qweather"]
        )

    def _stock(self, target: str) -> ToolResult:
        """获取股票行情 - 使用 provider chain (Sina -> Tavily)"""
        if not target:
            return ToolResult(
                ok=False, 
                text="请提供股票代码或名称（如：上证指数、600519、贵州茅台）", 
                error="missing_symbol"
            )
        
        # Use provider chain if available
        if hasattr(self, 'use_get_stock_chain') and self.use_get_stock_chain and self.get_stock_chain:
            try:
                result = self.get_stock_chain.execute("get_stock", query=target)
                
                if result.ok and result.data:
                    # Add fallback chain info if present
                    if result.fallback_chain:
                        if result.data.raw is None:
                            result.data.raw = {}
                        result.data.raw["fallback_chain"] = result.fallback_chain
                    return result.data
                
                # All providers failed, fallback to web_search
                return self._fallback_to_web_search(
                    original_tool="get_stock",
                    query=f"{target} 股票",
                    error=result.error or "all_providers_failed",
                    fallback_chain=result.fallback_chain if result.fallback_chain else ["get_stock_chain"]
                )
                
            except Exception as e:
                print(f"Provider chain error: {e}, falling back to legacy")
                # Fall through to legacy implementation
        
        # Legacy implementation (fallback if provider chain not available)
        # 转换为新浪格式代码
        symbol = normalize_to_sina_symbol(target)
        
        if not symbol:
            return ToolResult(
                ok=False, 
                text="请提供股票代码或名称（如：上证指数、600519、贵州茅台）", 
                error="missing_symbol"
            )
        
        # 调用新浪财经API
        result = self.sina_finance.get_stock_quote(symbol)
        
        if not result.success:
            # 失败时尝试web search fallback
            return self._fallback_to_web_search(
                original_tool="get_stock",
                query=f"{target} 股票 最新行情",
                error=result.error,
                fallback_chain=["sina_finance"],
            )
        
        # 格式化显示文本
        quote_data = result.data["quote"]
        text = format_stock_display(quote_data, symbol, target)
        
        return ToolResult(
            ok=True,
            text=text,
            raw={
                "provider": "sina_finance",
                "symbol": symbol,
                "quote": quote_data,
            },
        )

    def _web_search(self, query: str) -> ToolResult:
        if not query:
            return ToolResult(ok=False, text="请提供搜索关键词", error="missing_query")
        
        # Use provider chain if available
        if self.use_provider_chain and self.web_search_chain:
            try:
                result = self.web_search_chain.execute("web_search", query=query)
                
                if result.ok and result.data:
                    # Add fallback chain info if present
                    if result.fallback_chain:
                        if result.data.raw is None:
                            result.data.raw = {}
                        result.data.raw["fallback_chain"] = result.fallback_chain
                    return result.data
                
                # All providers failed, return error
                return ToolResult(
                    ok=False,
                    text=f"搜索{query}失败，请稍后重试",
                    error=result.error or "all_providers_failed"
                )
                
            except Exception as e:
                print(f"Provider chain error: {e}, falling back to legacy")
                # Fall through to legacy implementation
        
        # Legacy implementation (fallback if provider chain not available)
        if not self.tavily_key:
            return ToolResult(
                ok=False,
                text="搜索服务暂不可用",
                error="no_tavily_key"
            )

        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": self.search_depth or "basic",
            "topic": "general",
            "max_results": max(1, self.search_max_results * 2),  # 获取更多结果用于过滤
        }
        try:
            # 使用 tavily_timeout 而非 self.timeout
            body = _http_post_json("https://api.tavily.com/search", payload, timeout=self.tavily_timeout)
            results = body.get("results") or []
            if not results:
                return ToolResult(ok=False, text=f"未检索到{query}的结果", error="no_results")

            # 使用 Result Processing 模块处理结果
            try:
                from infra.tool_clients.search_result_processor import process_search_results
            except ImportError:
                from agent_service.infra.tool_clients.search_result_processor import process_search_results
            
            processed = process_search_results(
                results,
                query=query,
                max_results=self.search_max_results,
                relevance_threshold=0.1  # 降低阈值从 0.3 到 0.1
            )

            if not processed:
                # 保底逻辑：至少返回相关性最高的 1 条
                if results:
                    best = max(results, key=lambda x: x.get('score', 0))
                    processed = [best]
                else:
                    return ToolResult(ok=False, text=f"未找到与{query}相关的结果", error="no_relevant_results")

            # 格式化输出（包含可信度信息）
            lines = []
            for i, r in enumerate(processed, 1):
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("snippet", "")[:self.search_snippet_chars]
                credibility = r.get("credibility", 5)

                # 添加可信度标记
                trust_mark = ""
                if credibility >= 9:
                    trust_mark = " [官方]"
                elif credibility >= 7:
                    trust_mark = " [可信]"

                lines.append(f"{i}. {title}{trust_mark} | {url} | {snippet}")

            text = f"已搜索{query}，结果如下：\n" + "\n".join(lines)
            return ToolResult(ok=True, text=text, raw={"provider": "tavily", "query": query, "results": processed})
        except (TimeoutError, urllib.error.URLError) as e:
            # 超时或网络错误时返回错误
            return ToolResult(
                ok=False,
                text=f"搜索超时，请稍后重试",
                error=f"tavily_timeout:{e}"
            )
        except Exception as e:  # noqa: BLE001
            return ToolResult(
                ok=False,
                text=f"搜索失败：{str(e)[:50]}",
                error=f"tavily_fail:{e}"
            )

    def _news(self, topic: str) -> ToolResult:
        """获取新闻 - 根据类别选择链路
        
        财经类新闻：Sina News（专用）
        通用新闻：Baidu Web Search（备用）
        """
        # 检测是否为财经类新闻
        is_finance = self._is_finance_news(topic)
        
        if is_finance:
            # 财经新闻链路
            if hasattr(self, 'use_get_news_finance_chain') and self.use_get_news_finance_chain and self.get_news_finance_chain:
                try:
                    result = self.get_news_finance_chain.execute("get_news", query=topic)
                    
                    if result.ok and result.data:
                        # 应用去重
                        result.data = self._deduplicate_news(result.data, topic)
                        
                        if result.fallback_chain:
                            if result.data.raw is None:
                                result.data.raw = {}
                            result.data.raw["fallback_chain"] = result.fallback_chain
                        return result.data
                    
                    # Sina失败，fallback到通用新闻
                    print(f"Finance news failed: {result.error}, trying general news")
                except Exception as e:
                    print(f"Finance news chain error: {e}, trying general news")
        
        # 通用新闻链路
        if hasattr(self, 'use_get_news_general_chain') and self.use_get_news_general_chain and self.get_news_general_chain:
            try:
                result = self.get_news_general_chain.execute("get_news_general", query=topic)
                
                if result.ok and result.data:
                    # 应用去重
                    result.data = self._deduplicate_news(result.data, topic)
                    
                    # 应用content_rewriter进行LLM重写
                    result.data = self._apply_news_rewrite(result.data, topic)
                    
                    if result.fallback_chain:
                        if result.data.raw is None:
                            result.data.raw = {}
                        result.data.raw["fallback_chain"] = result.fallback_chain
                    return result.data
                
                # 所有新闻源失败，fallback到web_search
                return self._fallback_to_web_search(
                    original_tool="get_news",
                    query=f"{topic} 新闻",
                    error=result.error or "all_news_providers_failed",
                    fallback_chain=result.fallback_chain if result.fallback_chain else ["get_news_general_chain"]
                )
                
            except Exception as e:
                print(f"General news chain error: {e}")
        
        # Fallback到web_search
        return self._fallback_to_web_search(
            original_tool="get_news",
            query=f"{topic} 新闻",
            error="news_chains_unavailable",
            fallback_chain=["get_news_finance_chain", "get_news_general_chain"]
        )
    
    def _is_finance_news(self, topic: str) -> bool:
        """检测是否为财经类新闻"""
        finance_keywords = [
            "财经", "金融", "股票", "股市", "基金", "期货", "外汇", 
            "经济", "市场", "投资", "A股", "港股", "美股", "上证", "深证",
            "涨跌", "行情", "市值", "IPO", "融资"
        ]
        return any(kw in topic for kw in finance_keywords)

    def _nearby(self, keyword: str, city: str | None, location: str | None = None) -> ToolResult:
        # Use provider chain if available
        if hasattr(self, 'use_find_nearby_chain') and self.use_find_nearby_chain and self.find_nearby_chain:
            try:
                result = self.find_nearby_chain.execute("find_nearby", keyword=keyword, city=city, location=location)
                
                if result.ok and result.data:
                    # Add fallback chain info if present
                    if result.fallback_chain:
                        if result.data.raw is None:
                            result.data.raw = {}
                        result.data.raw["fallback_chain"] = result.fallback_chain
                    return result.data
                
                # All providers failed, fallback to web_search
                return self._fallback_to_web_search(
                    original_tool="find_nearby",
                    query=f"{city or '当前位置'} {keyword}",
                    error=result.error or "all_providers_failed",
                    fallback_chain=result.fallback_chain if result.fallback_chain else ["find_nearby_chain"]
                )
                
            except Exception as e:
                print(f"Provider chain error: {e}, falling back to legacy")
                # Fall through to legacy implementation
        
        # Legacy implementation (fallback if provider chain not available)
        if self.amap_mcp:
            try:
                return self.amap_mcp.find_nearby(keyword=keyword, city=city, location=location)
            except Exception as e:
                print(f"Amap MCP failed: {e}, falling back to web_search")
        
        # Fallback to web_search
        loc = city or "当前位置"
        return self._fallback_to_web_search(
            original_tool="find_nearby",
            query=f"{loc} 附近 {keyword}",
            error="amap_mcp_unavailable",
            fallback_chain=["amap_mcp"]
        )


    def _trip(self, destination: str, days: int = 2, travel_mode: str = "transit") -> ToolResult:
            """Plan a trip itinerary using Amap MCP.

            Args:
                destination: Destination city
                days: Number of days (default: 2)
                travel_mode: Travel mode ("transit" or "driving", default: "transit")

            Returns:
                ToolResult with trip itinerary
            """
            if not destination:
                return ToolResult(ok=False, text="缺少目的地", error="missing_destination")

            # Check if Amap MCP is available
            if not self.amap_mcp:
                return self._fallback_to_llm(
                    original_tool="plan_trip",
                    query=f"{destination} {days}日游",
                    error="amap_mcp_unavailable",
                    fallback_chain=["plan_trip"]
                )

            # Check if already in async context
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # Already in async context - cannot use asyncio.run()
                return ToolResult(
                    ok=False,
                    text="行程规划功能暂时不可用",
                    error="async_context_conflict"
                )
            except RuntimeError:
                # No running loop - safe to use asyncio.run()
                pass

            # Import plan_trip tool
            from domain.trip.tool import plan_trip

            # Call async plan_trip
            result = asyncio.run(plan_trip(
                destination=destination,
                days=days,
                travel_mode=travel_mode,
                amap_client=self.amap_mcp
            ))

            # Apply LLM post-processing if result is ok
            if result.ok:
                result = self._apply_llm_rewrite(result, destination, days, travel_mode)

            return result

    def _fallback_to_web_search(
        self,
        original_tool: str,
        query: str,
        error: str,
        fallback_chain: list[str] | None = None,
    ) -> ToolResult:
        """Fallback to web search when primary tool fails.
        
        Args:
            original_tool: Original tool name
            query: Search query
            error: Error from original tool
            fallback_chain: List of failed providers
            
        Returns:
            ToolResult from web search
        """
        result = self._web_search(query)
        
        # Add fallback chain info
        if result.raw is None:
            result.raw = {}
        
        chain = fallback_chain or [original_tool]
        result.raw["fallback_chain"] = chain
        result.raw["original_tool"] = original_tool
        result.raw["original_error"] = error
        
        # Set result_quality
        result.result_quality = "fallback_search"
        
        return result
    
    def _fallback_to_llm(
        self,
        original_tool: str,
        query: str,
        error: str,
        fallback_chain: list[str] | None = None,
    ) -> ToolResult:
        """Fallback to LLM when all providers fail.
        
        Args:
            original_tool: Original tool name
            query: User query
            error: Error from original tool
            fallback_chain: List of failed providers
            
        Returns:
            ToolResult with LLM-generated response
        """
        try:
            from infra.llm_clients.lm_studio_client import LMStudioClient
            
            llm = LMStudioClient()
            
            # Generate LLM response
            response = llm.generate(
                user_query=query,
                system_prompt="你是一个有帮助的助手。请根据用户的查询提供有用的信息。"
            )
            
            result = ToolResult(
                ok=True,
                text=response,
                raw={
                    "provider": "llm_fallback",
                    "original_tool": original_tool,
                    "original_error": error,
                    "fallback_chain": fallback_chain or [original_tool],
                },
                result_quality="fallback_llm",
            )
            
            return result
            
        except Exception as e:
            # If LLM also fails, return error
            return ToolResult(
                ok=False,
                text=f"无法获取{query}的信息，请稍后重试",
                error=f"all_fallbacks_failed:{error}",
                raw={
                    "original_tool": original_tool,
                    "original_error": error,
                    "llm_error": str(e),
                    "fallback_chain": fallback_chain or [original_tool],
                },
                result_quality="fallback_llm",
            )

    def _deduplicate_news(self, result: ToolResult, topic: str) -> ToolResult:
        """对新闻结果进行去重
        
        Args:
            result: 原始新闻结果
            topic: 查询主题
            
        Returns:
            去重后的结果
        """
        import hashlib
        
        # 初始化该query的缓存
        if topic not in self._news_cache:
            self._news_cache[topic] = set()
        
        # 从raw中获取新闻列表
        if not result.raw or "results" not in result.raw:
            return result
        
        original_results = result.raw["results"]
        filtered_results = []
        
        for news in original_results:
            title = news.get("title", "").strip()
            if not title:
                continue
            
            # 计算标题hash
            title_hash = hashlib.md5(title.encode()).hexdigest()
            
            # 检查是否已返回过
            if title_hash not in self._news_cache[topic]:
                filtered_results.append(news)
                self._news_cache[topic].add(title_hash)
        
        # 如果过滤后没有结果，清空缓存重新开始
        if not filtered_results:
            print(f"All news filtered as duplicates for '{topic}', clearing cache")
            self._news_cache[topic].clear()
            filtered_results = original_results[:3]  # 返回前3条
            for news in filtered_results:
                title = news.get("title", "").strip()
                if title:
                    title_hash = hashlib.md5(title.encode()).hexdigest()
                    self._news_cache[topic].add(title_hash)
        
        # 更新结果
        result.raw["results"] = filtered_results
        
        # 重新格式化text
        lines = []
        for i, r in enumerate(filtered_results, 1):
            title = r.get("title", "").strip()
            snippet = r.get("snippet", "").strip()
            
            # 截断摘要到合理长度（约50字）
            if len(snippet) > 100:
                snippet = snippet[:100].rstrip() + "..."
            
            lines.append(f"{i}. {title}\n{snippet}")
        
        result.text = f"已搜索{topic}，结果如下：\n" + "\n\n".join(lines)
        
        return result

    def _apply_news_rewrite(self, result: ToolResult, topic: str) -> ToolResult:
        """Apply LLM rewriting to news result.

        Args:
            result: Original tool result
            topic: News topic

        Returns:
            ToolResult with rewritten text
        """
        try:
            from infra.llm_clients.lm_studio_client import LMStudioClient
            import logging

            logger = logging.getLogger(__name__)
            llm = LMStudioClient()

            system_prompt = """你是新闻摘要助手。将新闻重写为口语化、简洁的格式。

规则：
1. 保持原有序号和标题
2. 摘要用口语化表达，30-50字
3. 可用"据说"、"看来"、"竟然"等词
4. 只输出新闻列表，不要其他内容

格式：
序号. 标题
摘要内容"""

            user_prompt = f"""原始新闻：
{result.text}

重写为口语化摘要："""

            rewritten_text = llm.generate(
                user_query=user_prompt,
                system_prompt=system_prompt
            )

            # Handle empty response from LLM
            if not rewritten_text or not rewritten_text.strip():
                logger.warning("LLM returned empty response for news rewrite, using original output")
                return result

            # Update result with rewritten text
            result.text = rewritten_text

            # Add rewrite metadata
            if result.raw is None:
                result.raw = {}
            result.raw["llm_rewritten"] = True

            return result

        except Exception as e:
            # If LLM fails, return original result
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"News LLM rewrite failed: {e}, using original output")
            return result

    def _apply_llm_rewrite(self, result: ToolResult, destination: str, days: int, travel_mode: str) -> ToolResult:
        """Apply LLM rewriting to trip result.

        Args:
            result: Original tool result
            destination: Destination city
            days: Number of days
            travel_mode: Travel mode

        Returns:
            ToolResult with rewritten text
        """
        try:
            from infra.llm_clients.lm_studio_client import LMStudioClient
            import logging

            logger = logging.getLogger(__name__)
            llm = LMStudioClient()

            system_prompt = """你是一个专业的旅游规划助手。你的任务是将结构化的行程信息重写为简洁、自然、易读的文本。

要求：
1. 输出长度严格控制在400字以内（约50%压缩）
2. 每天行程只保留2-3个核心景点，省略次要景点
3. 只输出景点名称，不要输出详细地址（如"虎园路25号"）
4. 保留原文中的具体交通时间信息（如"建议预留20分钟"、"建议预留30分钟"）
5. 不要把所有交通时间统一成"建议预留30分钟"，要保留原文的差异
6. 如果原文包含餐厅推荐，请在每天行程末尾简洁列出（格式：今日精选餐厅：A、B、C）
7. 餐厅推荐只说名称，不要生成"距离X仅X分钟"、"就在附近"等位置相关描述
8. 使用简洁的语言，避免冗长描述
9. 不要添加原文中没有的信息
10. 直接输出重写后的文本，不要输出思考过程

示例格式：
{destination}{days}日游行程：

第1天：上午游览A景点（建议预留20分钟）、B景点（建议预留30分钟），下午前往C景点。今日精选餐厅：X餐厅、Y餐厅、Z餐厅。
第2天：上午参观D景点（建议预留25分钟）、E景点，下午体验F景点。今日精选餐厅：P餐厅、Q餐厅、R餐厅。"""

            user_prompt = f"""用户查询: {destination}{days}日游

工具返回的原始行程信息:
{result.text}

请将上述行程信息重写为自然、友好的文本，让用户更容易理解和使用。"""

            rewritten_text = llm.generate(
                user_query=user_prompt,
                system_prompt=system_prompt
            )

            # Update result with rewritten text
            result.text = rewritten_text

            # Add rewrite metadata
            if result.raw is None:
                result.raw = {}
            result.raw["llm_rewritten"] = True

            return result

        except Exception as e:
            # If LLM fails, return original result
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LLM rewrite failed: {e}, using original output")
            return result





    def _qweather_lookup_city_id(self, city: str) -> str | None:
        base_host = self.qweather_host or "geoapi.qweather.com"
        url = f"https://{base_host}/geo/v2/city/lookup?" + urllib.parse.urlencode({"location": city})
        headers = {"X-QW-Api-Key": self.qweather_key}
        body = _http_get_json(url, timeout=self.timeout, headers=headers)
        loc = body.get("location") or []
        if not loc:
            return None
        return str(loc[0].get("id") or "") or None

    def _qweather_now(self, city_id: str) -> dict[str, Any]:
        base_host = self.qweather_host or "devapi.qweather.com"
        url = f"https://{base_host}/v7/weather/now?" + urllib.parse.urlencode({"location": city_id})
        headers = {"X-QW-Api-Key": self.qweather_key}
        return _http_get_json(url, timeout=self.timeout, headers=headers)

    def _qweather_3d(self, city_id: str) -> dict[str, Any]:
        base_host = self.qweather_host or "devapi.qweather.com"
        url = f"https://{base_host}/v7/weather/3d?" + urllib.parse.urlencode({"location": city_id})
        headers = {"X-QW-Api-Key": self.qweather_key}
        return _http_get_json(url, timeout=self.timeout, headers=headers)

    def _eastmoney_quote(self, symbol: str) -> ToolResult | None:
        secid = _to_eastmoney_secid(symbol)
        if not secid:
            return None
        url = "https://push2.eastmoney.com/api/qt/stock/get?" + urllib.parse.urlencode(
            {
                "secid": secid,
                "fields": "f57,f58,f43,f44,f45,f46,f47,f48,f170,f171",
            }
        )
        try:
            body = _http_get_json(url, timeout=self.timeout)
            data = body.get("data") or {}
            if not data:
                return None

            code = str(data.get("f57") or "")
            name = str(data.get("f58") or "")
            price = _em_price(data.get("f43"))
            high = _em_price(data.get("f44"))
            low = _em_price(data.get("f45"))
            open_px = _em_price(data.get("f46"))
            volume = data.get("f47")
            amount = data.get("f48")
            chg_pct = _em_pct(data.get("f170"))
            chg = _em_price(data.get("f171"))

            text = (
                f"{name or symbol}（{code or symbol}）最新 {price}，涨跌 {chg}（{chg_pct}%）；"
                f"开盘 {open_px}，最高 {high}，最低 {low}，成交量 {volume}，成交额 {amount}。"
            )
            return ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "eastmoney",
                    "symbol": symbol,
                    "secid": secid,
                    "quote": data,
                },
            )
        except Exception:
            return None

    def _tencent_quote(self, symbol: str) -> ToolResult | None:
        qcode = _to_tencent_symbol(symbol)
        if not qcode:
            return None
        url = "https://qt.gtimg.cn/q=" + urllib.parse.quote(qcode)
        try:
            text = _http_get_text(url, timeout=self.timeout, encoding="gbk")
            if "\"" not in text:
                return None
            payload = text.split("\"", 1)[1].rsplit("\"", 1)[0]
            parts = payload.split("~")
            if len(parts) < 35:
                return None
            name = parts[1] if len(parts) > 1 else symbol
            code = parts[2] if len(parts) > 2 else symbol
            price = parts[3] if len(parts) > 3 else "-"
            prev_close = parts[4] if len(parts) > 4 else "-"
            open_px = parts[5] if len(parts) > 5 else "-"
            volume = parts[6] if len(parts) > 6 else "-"
            trade_time = parts[30] if len(parts) > 30 else "-"
            chg = parts[31] if len(parts) > 31 else "-"
            chg_pct = parts[32] if len(parts) > 32 else "-"
            high = parts[33] if len(parts) > 33 else "-"
            low = parts[34] if len(parts) > 34 else "-"

            text_out = (
                f"{name}（{code}）最新 {price}，涨跌 {chg}（{chg_pct}%）；"
                f"开盘 {open_px}，最高 {high}，最低 {low}，昨收 {prev_close}，成交量 {volume}，时间 {trade_time}。"
            )
            return ToolResult(
                ok=True,
                text=text_out,
                raw={
                    "provider": "tencent_quote",
                    "symbol": symbol,
                    "qcode": qcode,
                    "parts": parts[:40],
                },
            )
        except Exception:
            return None

    def _stock_display_name(self, symbol: str, target: str) -> str:
        name_code = self._tencent_name_code(symbol)
        if name_code:
            name, code = name_code
            return f"{name}（{code}）"
        zh_name = _stock_name_from_target(target)
        if zh_name:
            return f"{zh_name}（{symbol}）"
        return symbol

    def _tencent_name_code(self, symbol: str) -> tuple[str, str] | None:
        qcode = _to_tencent_symbol(symbol)
        if not qcode:
            return None
        url = "https://qt.gtimg.cn/q=" + urllib.parse.quote(qcode)
        try:
            text = _http_get_text(url, timeout=self.timeout, encoding="gbk")
            if "\"" not in text:
                return None
            payload = text.split("\"", 1)[1].rsplit("\"", 1)[0]
            parts = payload.split("~")
            if len(parts) < 3:
                return None
            name = str(parts[1] or "").strip()
            code = str(parts[2] or "").strip()
            if not name:
                return None
            return name, code or symbol
        except Exception:
            return None


    def invoke_with_intent(
        self,
        tool_name: str,
        query: str,
    ) -> tuple[ToolResult, Any]:
        """Invoke tool with location intent parsing, reranking, and template response.

        Args:
            tool_name: Tool name
            query: User query (should be rewritten query)

        Returns:
            (ToolResult, LocationIntent or None)
        """
        from domain.location.intent import LocationIntent
        from domain.location.parser import parse_location_intent
        from domain.location.capability import get_retrieval_source, RetrievalSource

        intent = None
        tool_args = {}

        # For find_nearby: parse location intent
        if tool_name == "find_nearby":
            intent = parse_location_intent(query)

            # Check completeness
            if not intent.is_complete():
                return (
                    ToolResult(
                        ok=False,
                        text="信息不完整，请提供地点和搜索目标",
                        error="incomplete_intent",
                        raw={"intent": intent.to_dict()},
                    ),
                    intent,
                )

            tool_args = intent.to_tool_args()
        else:
            # For other tools: use existing logic
            tool_args = {
                k: v
                for k, v in {
                    "keyword": query,
                    "city": None,
                    "topic": query,
                    "target": query,
                    "destination": query,
                    "query": query,
                }.items()
                if v is not None
            }

        # Invoke tool
        result = self.invoke(tool_name=tool_name, tool_args=tool_args)

        # Check if we got no results and should try alternative source
        if tool_name == "find_nearby" and intent and not result.ok:
            retrieval_source = get_retrieval_source(intent.category)
            if retrieval_source == RetrievalSource.WEB_SEARCH:
                # Category not well-supported by Amap, explain to user
                result = ToolResult(
                    ok=False,
                    text=f"该区域暂无{intent.category}相关信息，建议扩大搜索范围或尝试其他方式查询。",
                    error="unsupported_category",
                    raw={"intent": intent.to_dict(), "suggested_source": "web_search"},
                )

        # Post-process: Rerank and format results for find_nearby
        if tool_name == "find_nearby" and intent and result.ok:
            result = self._rerank_and_format_results(result, intent)

        # Attach intent to result if available
        if intent:
            if result.raw is None:
                result.raw = {}
            result.raw["intent"] = intent.to_dict()

        return result, intent

    def invoke_nearby_with_intent(
        self,
        query: str,
        city: str | None = None,
    ) -> tuple[ToolResult, Any]:
        """Invoke find_nearby with location intent parsing, reranking, and template response.

        Args:
            query: User query
            city: Optional city override

        Returns:
            (ToolResult, LocationIntent)
        """
        from domain.location.parser import parse_location_intent

        intent = parse_location_intent(query)

        # Override city if provided
        if city:
            intent.city = city

        # Check completeness
        if not intent.is_complete():
            return (
                ToolResult(
                    ok=False,
                    text="信息不完整，请提供地点和搜索目标",
                    error="incomplete_intent",
                    raw={"intent": intent.to_dict()},
                ),
                intent,
            )

        # Invoke with tool args
        tool_args = intent.to_tool_args()
        result = self.invoke(tool_name="find_nearby", tool_args=tool_args)

        # Post-process: Rerank and format results
        if result.ok:
            result = self._rerank_and_format_results(result, intent)

        # Attach intent to result
        if result.raw is None:
            result.raw = {}
        result.raw["intent"] = intent.to_dict()

        return result, intent

    def _rerank_and_format_results(self, result: ToolResult, intent: Any) -> ToolResult:
        """Rerank, filter, and format results based on intent.

        Args:
            result: Original tool result
            intent: Parsed location intent

        Returns:
            Tool result with reranked data and formatted text
        """
        from domain.location.result_processor import create_default_processor_chain
        from domain.location.templates import can_use_template, format_location_results

        # Extract POI list from result
        raw_data = result.raw or {}
        pois = raw_data.get("pois", [])

        if not pois:
            return result

        original_count = len(pois)

        # Step 1: Rerank using processor chain
        chain = create_default_processor_chain()
        processed_pois = chain.process(pois, intent)

        # Step 2: Format using templates
        if can_use_template(processed_pois):
            formatted_text = format_location_results(
                processed_pois,
                intent,
                original_count if len(processed_pois) != original_count else None
            )
        else:
            # Fallback: use original text
            formatted_text = result.text

        # Update result
        new_raw = dict(raw_data)
        new_raw["pois"] = processed_pois
        new_raw["original_count"] = original_count
        new_raw["filtered_count"] = len(processed_pois)
        new_raw["used_template"] = can_use_template(processed_pois)

        return ToolResult(
            ok=result.ok,
            text=formatted_text,
            error=result.error,
            raw=new_raw,
        )



def _http_get_json(url: str, timeout: float, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req_headers = {"User-Agent": "agent-service/0.1", "Accept-Encoding": "gzip"}
    if headers:
        req_headers.update(headers)
    last_err: Exception | None = None
    for _ in range(2):
        req = urllib.request.Request(url, headers=req_headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                if (resp.headers.get("Content-Encoding") or "").lower() == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("http_get_json_failed")


def _http_post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "agent-service/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_text(
    url: str,
    timeout: float,
    encoding: str = "utf-8",
    headers: dict[str, str] | None = None,
) -> str:
    req_headers = {"User-Agent": "agent-service/0.1", "Accept-Encoding": "gzip"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if (resp.headers.get("Content-Encoding") or "").lower() == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode(encoding, errors="replace")


def _normalize_stock_symbol(target: str) -> str:
    s = target.strip().upper()
    # Common CN phrasing fallback.
    mapping = {
        "苹果": "AAPL",
        "京东": "JD",
        "特斯拉": "TSLA",
        "英伟达": "NVDA",
        "微软": "MSFT",
        "亚马逊": "AMZN",
        "谷歌": "GOOGL",
        "贵州茅台": "600519.SS",
        "茅台": "600519.SS",
        "上证指数": "000001.SS",
        "上证": "000001.SS",
        "深证指数": "399001.SZ",
        "深证成指": "399001.SZ",
        "创业板指数": "399006.SZ",
        "沪深300": "000300.SS",
        "恒生指数": "HSI",
        "纳斯达克指数": "IXIC",
        "道琼斯指数": "DJI",
        "标普500": "SPX",
    }
    if s in mapping:
        return mapping[s]

    # Direct symbol candidates like AAPL, TSLA, 000001.SS, 0700.HK
    cleaned = s
    for rm in ("股价", "股票", "行情", "价格", "最新", "现在", "查询", "查一下", "查", "一下", "涨跌", "怎么样", "情况"):
        cleaned = cleaned.replace(rm, " ")

    for token in cleaned.replace("，", " ").replace(",", " ").split():
        token = token.strip()
        if not token:
            continue
        if token.isascii() and token.isalpha() and 1 <= len(token) <= 8:
            return token
        if "." in token and len(token) <= 12:
            return token
        if token.isdigit() and len(token) == 6:
            if token.startswith("6"):
                return f"{token}.SS"
            if token.startswith(("0", "3")):
                return f"{token}.SZ"

    # Chinese mention fallback.
    for zh, sym in mapping.items():
        if zh in target:
            return sym
    return ""


def _stock_fallback_query(target: str, symbol: str) -> str:
    t = target.strip()
    if symbol:
        return f"{symbol} {t or '股票'} 最新行情"
    return f"{t or '股票'} 最新行情"


def _to_eastmoney_secid(symbol: str) -> str | None:
    s = symbol.strip().upper()
    if "." not in s:
        return None
    code, market = s.split(".", 1)
    if not code.isdigit():
        return None
    if market == "SS":
        return f"1.{code}"
    if market == "SZ":
        return f"0.{code}"
    return None


def _to_tencent_symbol(symbol: str) -> str | None:
    s = symbol.strip().upper()
    if "." not in s:
        return None
    code, market = s.split(".", 1)
    if not code.isdigit():
        return None
    if market == "SS":
        return f"sh{code}"
    if market == "SZ":
        return f"sz{code}"
    return None


def _em_price(v: object) -> str:
    try:
        return f"{float(v) / 100:.2f}"
    except Exception:
        return "-"


def _em_pct(v: object) -> str:
    try:
        return f"{float(v) / 100:.2f}"
    except Exception:
        return "-"


def _pack_search_results(results: list[dict[str, Any]], max_results: int, snippet_chars: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in results[:max(1, max_results)]:
        title = str(item.get("title") or "无标题").replace("\n", " ").strip()
        url = str(item.get("url") or "").strip()
        content = str(item.get("content") or "").replace("\n", " ").strip()
        snippet = content[:snippet_chars] + ("..." if len(content) > snippet_chars else "")
        out.append({"title": title, "url": url, "snippet": snippet})
    return out


def _stock_name_from_target(target: str) -> str | None:
    mapping = {
        "茅台": "贵州茅台",
        "贵州茅台": "贵州茅台",
        "上证指数": "上证指数",
        "深证成指": "深证成指",
        "深证指数": "深证指数",
        "创业板指数": "创业板指数",
    }
    t = target.strip()
    for k, v in mapping.items():
        if k in t:
            return v
    return None


def _with_fallback_chain(res: ToolResult, chain: list[str]) -> ToolResult:
    raw = dict(res.raw or {})
    existing = raw.get("fallback_chain")
    merged: list[str] = []
    if isinstance(existing, list):
        for item in existing:
            if isinstance(item, str) and item and item not in merged:
                merged.append(item)
    for item in chain:
        if item and item not in merged:
            merged.append(item)
    raw["fallback_chain"] = merged
    res.raw = raw
    return res


