from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RewriteResult:
    effective_query: str
    rewritten: bool
    source: str = "none"


def rewrite_query(query: str, session_ctx: dict[str, object]) -> RewriteResult:
    q = query.strip()
    if not q or not session_ctx:
        return RewriteResult(effective_query=q, rewritten=False)

    city = _as_str(session_ctx.get("last_city"))
    last_tool = _as_str(session_ctx.get("last_tool"))
    last_topic = _as_str(session_ctx.get("last_topic"))
    last_target = _as_str(session_ctx.get("last_target"))
    last_destination = _as_str(session_ctx.get("last_destination"))

    # A) Follow-up shorthand should inherit last tool domain first.
    if _is_followup_short(q) and last_tool:
        rebuilt = _rebuild_from_last_tool(last_tool, city, last_topic, last_target, last_destination)
        if rebuilt:
            return RewriteResult(effective_query=rebuilt, rewritten=True, source="followup_intent")

    # B) Deictic location resolution: 那边/那里 -> last_city
    if city and any(k in q for k in ("那边", "那里", "那儿", "这边", "这里")):
        rewritten = q
        for k in ("那边", "那里", "那儿", "这边", "这里"):
            rewritten = rewritten.replace(k, city)
        return RewriteResult(effective_query=rewritten, rewritten=True, source="coref_city")

    # C) City + generic ask, inherit previous tool domain
    if city and _is_generic_ask(q) and last_tool:
        rebuilt = _rebuild_from_last_tool(last_tool, city, last_topic, last_target, last_destination)
        if rebuilt:
            return RewriteResult(effective_query=rebuilt, rewritten=True, source="city_plus_followup")

    return RewriteResult(effective_query=q, rewritten=False)


def _is_followup_short(q: str) -> bool:
    keys = ("继续", "再查", "再看", "再来", "帮我查查", "查查", "看下", "看看")
    if len(q) <= 12 and any(k in q for k in keys):
        return True
    return q in {"然后呢", "接着来", "继续吧", "那这个呢"}


def _is_generic_ask(q: str) -> bool:
    keys = ("帮我查", "查查", "看看", "看下", "查一下")
    return any(k in q for k in keys)


def _rebuild_from_last_tool(
    last_tool: str,
    city: str,
    topic: str,
    target: str,
    destination: str,
) -> str:
    if last_tool == "get_weather" and city:
        return f"{city}今天天气怎么样"
    if last_tool == "get_news":
        t = topic or "今日热点"
        return f"查一下{t}新闻"
    if last_tool == "get_stock":
        t = target or "上证指数"
        return f"查一下{t}最新行情"
    if last_tool == "plan_trip":
        d = destination or city
        if d:
            return f"帮我规划去{d}的行程"
    if last_tool == "find_nearby":
        if city:
            return f"查{city}附近的餐厅"
        return "查我附近的餐厅"
    if last_tool == "web_search":
        t = topic or target
        if t:
            return f"帮我搜索{t}"
    return ""


def _as_str(v: object) -> str:
    if isinstance(v, str):
        return v
    return ""
