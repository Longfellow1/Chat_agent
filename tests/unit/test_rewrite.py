from __future__ import annotations

from app.orchestrator.rewrite import rewrite_query


def test_city_coref() -> None:
    r = rewrite_query("那边天气呢", {"last_city": "郑州"})
    assert r.rewritten is True
    assert "郑州" in r.effective_query


def test_followup_by_tool() -> None:
    r = rewrite_query("再查一下", {"last_tool": "get_weather", "last_city": "北京"})
    assert r.rewritten is True
    assert r.effective_query == "北京今天天气怎么样"
