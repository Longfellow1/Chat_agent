"""Baidu Maps MCP client for location services.

Implementation follows AmapMCPClient pattern for consistency.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import Any

from domain.tools.types import ToolResult


class BaiduMapsMCPClient:
    """Client for Baidu Maps MCP server.
    
    This implementation follows the same pattern as AmapMCPClient to ensure
    consistent process management and error handling.
    """
    
    def __init__(self) -> None:
        self.api_key = os.getenv("BAIDU_MAP_API_KEY", "").strip()
        self.process: subprocess.Popen | None = None
        self._started = False
    
    def _ensure_started(self) -> None:
        """Ensure MCP server is started."""
        if self._started:
            return
        
        if not self.api_key:
            raise RuntimeError("BAIDU_MAPS_API_KEY not configured")
        
        # Start MCP server process (same pattern as Amap)
        env = os.environ.copy()
        env["BAIDU_MAP_API_KEY"] = self.api_key
        
        self.process = subprocess.Popen(
            ["npx", "-y", "@baidumap/mcp-server-baidu-map"],
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
        
        # Build JSON-RPC request (same as Amap)
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
        """Find nearby POIs using Baidu Maps MCP.
        
        Args:
            keyword: Search keyword (e.g., "停车场", "餐厅")
            city: City name (e.g., "上海")
            location: Location coordinates (e.g., "121.445,31.227")
        
        Returns:
            ToolResult with POI data
        """
        try:
            # Build arguments for map_search_places
            arguments: dict[str, Any] = {
                "query": keyword,
                "region": city or "全国",
            }
            
            if location:
                arguments["location"] = location
                arguments["radius"] = 3000  # 3km radius
            
            # Call map_search_places tool
            result = self.call_tool("map_search_places", arguments)
            
            # Parse result (same pattern as Amap)
            content = result.get("content", [])
            if not content:
                return ToolResult(ok=False, text=f"未找到{city or '附近'}的{keyword}", error="no_results")
            
            # Extract POIs from content
            pois_text = content[0].get("text", "")
            pois_data = json.loads(pois_text) if isinstance(pois_text, str) else pois_text
            
            # Baidu uses "results" instead of "pois"
            pois = pois_data.get("results", [])
            
            if not pois:
                return ToolResult(ok=False, text=f"未找到{city or '附近'}的{keyword}", error="no_results")
            
            return ToolResult(
                ok=True,
                text=self._format_pois(pois[:10]),
                raw={"provider": "baidu_maps_mcp", "pois": pois[:10], "keyword": keyword, "city": city},
            )
        
        except Exception as e:
            return ToolResult(ok=False, text=f"百度地图MCP调用失败: {e}", error=str(e))
    
    def _format_pois(self, pois: list[dict[str, Any]]) -> str:
        """Format POI list to text (same as Amap)."""
        lines = []
        for i, poi in enumerate(pois[:3], 1):
            name = poi.get("name", "未知")
            address = poi.get("address", "")
            distance = poi.get("distance", "")
            
            suffix = f"，距离{distance}米" if distance else ""
            lines.append(f"{i}. {name}（{address}{suffix}）".strip())
        
        return "\n".join(lines)
    
    def close(self) -> None:
        """Close MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self._started = False
