"""Amap tool providers."""

from __future__ import annotations

import os

from domain.tools.types import ToolResult
from infra.tool_clients.amap_mcp_client import AmapMCPClient
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ToolProvider


class AmapMCPProvider(ToolProvider):
    """Amap MCP provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client: AmapMCPClient | None = None
        
        # Initialize client if API key available
        api_key = os.getenv("AMAP_API_KEY", "").strip()
        if api_key:
            try:
                self.client = AmapMCPClient()
            except Exception as e:
                print(f"Warning: Failed to initialize Amap MCP client: {e}")
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute find_nearby via Amap MCP."""
        if not self.client:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="amap_mcp_not_initialized",
            )
        
        keyword = kwargs.get("keyword", "")
        city = kwargs.get("city")
        location = kwargs.get("location")
        
        try:
            result = self.client.find_nearby(
                keyword=keyword,
                city=city,
                location=location,
            )
            
            return ProviderResult(
                ok=result.ok,
                data=result,
                provider_name=self.config.name,
                error=result.error if not result.ok else None,
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"amap_mcp_error:{e}",
            )
    
    def health_check(self) -> bool:
        """Check if Amap MCP is healthy."""
        if not self.client:
            return False
        
        try:
            result = self.client.find_nearby(keyword="测试", city="北京")
            return result.ok
        except Exception:
            return False


class AmapDirectProvider(ToolProvider):
    """Amap direct API provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("AMAP_API_KEY", "").strip()
        self.timeout = config.timeout
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute find_nearby via Amap direct API."""
        if not self.api_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="amap_api_key_missing",
            )
        
        keyword = kwargs.get("keyword", "")
        city = kwargs.get("city")
        
        # Use existing Amap API logic from MCPToolGateway
        # This is a simplified version - full implementation would mirror _nearby method
        try:
            import urllib.parse
            import urllib.request
            import json
            
            params = {
                "key": self.api_key,
                "keywords": keyword,
                "offset": 10,
                "page": 1,
                "extensions": "base",
            }
            if city:
                params["city"] = city
                params["citylimit"] = "true"
            
            url = "https://restapi.amap.com/v3/place/text?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "agent-service/0.1"})
            
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            
            pois = body.get("pois") or []
            if not pois:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_poi_results",
                )
            
            # Format result
            lines = []
            for i, poi in enumerate(pois[:3], 1):
                name = poi.get("name") or "未知地点"
                addr = poi.get("address") or ""
                dist = poi.get("distance") or ""
                poi_type = poi.get("type") or ""
                tel = poi.get("tel") or ""
                suffix = f"，距离{dist}米" if dist else ""
                lines.append(f"{i}. {name}（{addr}{suffix}） 类型：{poi_type} 电话：{tel}".strip())
            
            text = f"{city or '附近'}的{keyword}推荐：\n" + "\n".join(lines)
            
            result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "amap_direct",
                    "keyword": keyword,
                    "city": city,
                    "pois": pois[:3],
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
            )
            
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"amap_direct_error:{e}",
            )
    
    def health_check(self) -> bool:
        """Check if Amap API key is available."""
        return bool(self.api_key)
