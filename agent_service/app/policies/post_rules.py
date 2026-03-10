from __future__ import annotations

from domain.tools.planner import extract_city

REALTIME_HINTS = ("天气", "新闻", "股", "股票", "指数", "附近", "周边", "航班", "高铁")


def should_block_free_realtime_reply(query: str, decision_mode: str, tool_name: str | None) -> bool:
    if decision_mode != "reply":
        return False
    if tool_name:
        return False
    return any(k in query for k in REALTIME_HINTS)


def realtime_guard_reply(query: str) -> str:
    if "天气" in query:
        city = extract_city(query)
        if city:
            return f"我需要调用天气工具获取实时数据。请稍等，我将为你查询{city}天气。"
        return "要查实时天气，请补充城市名称，例如“郑州今天天气怎么样”。"
    if "新闻" in query:
        return "要给你实时新闻，我需要调用新闻工具。你可以说“查今天科技新闻”。"
    if "股" in query or "股票" in query or "指数" in query:
        return "要给你实时行情，我需要调用股票工具。请补充标的，例如“查贵州茅台股价”。"
    if "附近" in query or "周边" in query:
        return "要查附近信息，我需要调用地图工具。请补充城市或当前位置。"
    return "这个问题需要实时数据源支持，我先不编造结果。请补充更具体信息，我将调用对应工具。"
