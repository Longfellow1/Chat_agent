from __future__ import annotations

import os

from app.orchestrator.chat_flow import _should_skip_post_llm
from infra.tool_clients.mcp_gateway import MCPToolGateway


def test_should_skip_post_llm_stock() -> None:
    assert _should_skip_post_llm(
        "get_stock",
        "上证指数（000001）最新 4162.88，涨跌 16.25（0.39%）；开盘 4128.90，最高 4166.23，最低 4128.36。",
        {"provider": "tencent_quote"},
    )


def test_should_skip_post_llm_search_like() -> None:
    assert _should_skip_post_llm("web_search", "已搜索，结果如下：1. ...", {"provider": "tavily"})
    assert _should_skip_post_llm("get_news", "相关新闻如下：1. ...", {"provider": "tavily_news"})
    assert _should_skip_post_llm("find_nearby", "附近推荐：1. ...", {"provider": "amap"})


def test_plan_trip_mock_provider_without_key() -> None:
    old = os.environ.get("TAVILY_API_KEY")
    try:
        os.environ.pop("TAVILY_API_KEY", None)
        g = MCPToolGateway()
        r = g.invoke("plan_trip", {"destination": "杭州"})
        assert r.ok
        assert r.raw.get("provider") == "mock_trip"
    finally:
        if old is not None:
            os.environ["TAVILY_API_KEY"] = old

