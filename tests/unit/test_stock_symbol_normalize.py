from __future__ import annotations

from infra.tool_clients.mcp_gateway import _normalize_stock_symbol, _stock_fallback_query, _to_tencent_symbol


def test_normalize_cn_index_symbol() -> None:
    assert _normalize_stock_symbol("上证指数今天走势") == "000001.SS"
    assert _normalize_stock_symbol("深证成指") == "399001.SZ"
    assert _normalize_stock_symbol("创业板指数") == "399006.SZ"


def test_normalize_cn_stock_code() -> None:
    assert _normalize_stock_symbol("600519 股价") == "600519.SS"
    assert _normalize_stock_symbol("000001 行情") == "000001.SZ"


def test_normalize_us_stock_symbol() -> None:
    assert _normalize_stock_symbol("AAPL 最新行情") == "AAPL"


def test_stock_fallback_query_prefers_symbol() -> None:
    q = _stock_fallback_query(target="上证指数今天走势", symbol="000001.SS")
    assert "000001.SS" in q


def test_tencent_symbol_mapping() -> None:
    assert _to_tencent_symbol("000001.SS") == "sh000001"
    assert _to_tencent_symbol("399001.SZ") == "sz399001"
