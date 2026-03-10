"""Amap MCP client for location services."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import Any

from domain.tools.types import ToolResult


class AmapMCPClient:
    """Client for Amap MCP server."""
    
    def __init__(self) -> None:
        self.api_key = os.getenv("AMAP_API_KEY", "").strip()
        self.process: subprocess.Popen | None = None
        self._started = False
    
    def _ensure_started(self) -> None:
        """Ensure MCP server is started."""
        if self._started:
            return
        
        if not self.api_key:
            raise RuntimeError("AMAP_API_KEY not configured")
        
        # Start MCP server process
        env = os.environ.copy()
        env["AMAP_MAPS_API_KEY"] = self.api_key
        
        self.process = subprocess.Popen(
            ["npx", "-y", "@amap/amap-maps-mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
        )
        self._started = True
    
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call MCP tool synchronously."""
        return asyncio.run(self.call_tool_async(tool_name, arguments))
    
    async def call_tool_async(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call MCP tool asynchronously."""
        self._ensure_started()
        
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MCP server not running")
        
        # Build JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        
        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")
        
        # Check for empty response before parsing
        response_line = response_line.strip()
        if not response_line:
            raise RuntimeError("Empty response from MCP server")
        
        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response from MCP server: {e}")
        
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        
        return response.get("result", {})
    
    def find_nearby(self, keyword: str, city: str | None = None, location: str | None = None) -> ToolResult:
        """Find nearby POIs using Amap MCP.
        
        Args:
            keyword: Search keyword (e.g., "咖啡厅", "星巴克")
            city: City name (e.g., "上海")
            location: Location name or coordinates (e.g., "静安寺" or "121.445,31.227")
        
        Returns:
            ToolResult with POI data
        """
        try:
            # Strategy: If location is provided, use around_search; otherwise use text_search
            if location:
                # Need to geocode location first if it's a name
                if "," not in location:
                    # Geocode location name to coordinates
                    geo_result = self.call_tool("maps_geo", {"address": location, "city": city or ""})
                    content = geo_result.get("content", [])
                    if not content:
                        return self._text_search(keyword, city)
                    
                    geocodes_text = content[0].get("text", "")
                    
                    # Parse coordinates from result
                    import json
                    try:
                        geo_data = json.loads(geocodes_text) if isinstance(geocodes_text, str) else geocodes_text
                        # MCP returns "return" field, not "geocodes"
                        geocodes = geo_data.get("return", [])
                        if not geocodes:
                            return self._text_search(keyword, city)
                        
                        # Find the one in the specified city
                        location_coords = None
                        for geocode in geocodes:
                            if city and city in geocode.get("city", ""):
                                location_coords = geocode.get("location", "")
                                break
                        
                        # If not found in city, use first result
                        if not location_coords and geocodes:
                            location_coords = geocodes[0].get("location", "")
                        
                        if not location_coords:
                            return self._text_search(keyword, city)
                        
                        location = location_coords
                    except:
                        return self._text_search(keyword, city)
                
                # Use around_search with coordinates
                arguments = {
                    "location": location,
                    "keywords": keyword,
                    "radius": "3000",
                }
                result = self.call_tool("maps_around_search", arguments)
            else:
                # Use text_search
                return self._text_search(keyword, city)
            
            # Parse result
            content = result.get("content", [])
            if not content:
                return ToolResult(ok=False, text=f"未找到{city or '附近'}的{keyword}", error="no_results")
            
            # Extract POIs from content
            pois_text = content[0].get("text", "")
            import json
            pois_data = json.loads(pois_text) if isinstance(pois_text, str) else pois_text
            pois = pois_data.get("pois", [])
            
            if not pois:
                return ToolResult(ok=False, text=f"未找到{city or '附近'}的{keyword}", error="no_results")
            
            return ToolResult(
                ok=True,
                text=self._format_pois(pois[:10]),
                raw={"provider": "amap_mcp", "pois": pois[:10], "keyword": keyword, "city": city},
            )
        
        except Exception as e:
            return ToolResult(ok=False, text=f"高德MCP调用失败: {e}", error=str(e))
    
    def _text_search(self, keyword: str, city: str | None) -> ToolResult:
        """Text search using MCP."""
        from domain.location.amap_type_codes import get_amap_type_code
        
        arguments: dict[str, Any] = {"keywords": keyword}
        if city:
            arguments["city"] = city
        
        # Add type code if available
        type_code = get_amap_type_code(keyword)
        if type_code:
            arguments["types"] = type_code
        
        result = self.call_tool("maps_text_search", arguments)
        
        # Parse result
        content = result.get("content", [])
        if not content:
            return ToolResult(ok=False, text=f"未找到{city or ''}的{keyword}", error="no_results")
        
        pois_text = content[0].get("text", "")
        import json
        pois_data = json.loads(pois_text) if isinstance(pois_text, str) else pois_text
        pois = pois_data.get("pois", [])
        
        if not pois:
            return ToolResult(ok=False, text=f"未找到{city or ''}的{keyword}", error="no_results")
        
        return ToolResult(
            ok=True,
            text=self._format_pois(pois[:10]),
            raw={"provider": "amap_mcp", "pois": pois[:10], "keyword": keyword, "city": city},
        )
    
    def _format_pois(self, pois: list[dict[str, Any]]) -> str:
        """Format POI list to text."""
        lines = []
        for i, poi in enumerate(pois[:3], 1):
            name = poi.get("name", "未知")
            address = poi.get("address", "")
            distance = poi.get("distance", "")
            poi_type = poi.get("type", "")
            tel = poi.get("tel", "")
            
            suffix = f"，距离{distance}米" if distance else ""
            lines.append(f"{i}. {name}（{address}{suffix}） 类型：{poi_type} 电话：{tel}".strip())
        
        return "\n".join(lines)
    
    def close(self) -> None:
        """Close MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self._started = False
    def get_weather(self, city: str) -> ToolResult:
        """Get weather forecast using Amap MCP.

        Args:
            city: City name (e.g., "上海", "北京")

        Returns:
            ToolResult with weather data
        """
        try:
            result = self.call_tool("maps_weather", {"city": city})

            # Parse result
            content = result.get("content", [])
            if not content:
                return ToolResult(ok=False, text=f"未找到{city}的天气信息", error="no_weather_data")

            # Extract weather data from content
            weather_text = content[0].get("text", "")
            import json
            weather_data = json.loads(weather_text) if isinstance(weather_text, str) else weather_text

            # Check data structure - forecasts is a list of daily forecasts
            if "forecasts" not in weather_data or not weather_data["forecasts"]:
                return ToolResult(ok=False, text=f"未找到{city}的天气预报", error="no_forecast_data")

            # forecasts is directly a list of daily forecasts
            casts = weather_data["forecasts"]

            if not casts:
                return ToolResult(ok=False, text=f"未找到{city}的天气预报", error="no_cast_data")

            # Format weather text
            today = casts[0] if len(casts) > 0 else {}
            tomorrow = casts[1] if len(casts) > 1 else {}

            text = (
                f"{city}今日预报：{today.get('dayweather', '-')}，"
                f"{today.get('nighttemp', '-')}~{today.get('daytemp', '-')}°C，"
                f"风向{today.get('daywind', '-')}，风力{today.get('daypower', '-')}级；"
                f"明日预报：{tomorrow.get('dayweather', '-')}，"
                f"{tomorrow.get('nighttemp', '-')}~{tomorrow.get('daytemp', '-')}°C。"
            )

            return ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "amap_mcp",
                    "city": weather_data.get("city", city),
                    "forecasts": casts[:4],  # Return 4-day forecast
                },
            )

        except Exception as e:
            return ToolResult(ok=False, text=f"高德MCP天气查询失败: {e}", error=str(e))

