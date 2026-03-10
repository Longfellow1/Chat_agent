from __future__ import annotations

from app.orchestrator.chat_flow import _infer_fallback_chain
from domain.tools.types import ToolResult
from infra.tool_clients.mcp_gateway import _with_fallback_chain


def test_with_fallback_chain_merge() -> None:
    r = ToolResult(ok=True, text="ok", raw={"provider": "tavily", "fallback_chain": ["alpha_vantage"]})
    out = _with_fallback_chain(r, ["alpha_vantage", "tencent_quote", "tavily"])
    assert out.raw.get("fallback_chain") == ["alpha_vantage", "tencent_quote", "tavily"]


def test_infer_fallback_chain() -> None:
    chain = _infer_fallback_chain({"fallback_chain": ["a", "b"]})
    assert chain == ["a", "b"]
    assert _infer_fallback_chain({}) == []

