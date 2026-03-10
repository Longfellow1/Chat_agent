from __future__ import annotations

from domain.intents.router import route_query
from domain.tools.planner import build_tool_plan


def test_weather_route() -> None:
    d = route_query("郑州今天天气怎么样")
    assert d.decision_mode == "tool_call"
    assert d.tool_name == "get_weather"


def test_weather_missing_city() -> None:
    plan = build_tool_plan("今天天气怎么样", "get_weather")
    assert plan.missing_slots == ["city"]


def test_weather_city_extracted() -> None:
    plan = build_tool_plan("郑州，帮我查查天气", "get_weather")
    assert plan.missing_slots == []
    assert plan.tool_args.get("city") == "郑州"


def test_news_route() -> None:
    d = route_query("给我看看今天科技新闻")
    assert d.tool_name == "get_news"
