from __future__ import annotations

from typing import Any

from infra.tool_clients.mcp_gateway import MCPToolGateway
from domain.tools.types import ToolResult


class ToolExecutor:
    def __init__(self) -> None:
        self.gateway = MCPToolGateway()

    def execute(self, tool_name: str, tool_args: dict[str, Any]) -> ToolResult:
        try:
            return self.gateway.invoke(tool_name=tool_name, tool_args=tool_args)
        except Exception as e:  # noqa: BLE001
            return ToolResult(ok=False, text="工具调用失败", error=str(e))
