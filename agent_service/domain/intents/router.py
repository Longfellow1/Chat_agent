from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RouteDecision:
    decision_mode: str
    intent_probs: dict[str, float]
    tool_name: str | None = None


@dataclass
class _Rule:
    tool: str
    strong_keywords: tuple[str, ...]
    weak_keywords: tuple[str, ...]
    patterns: tuple[re.Pattern[str], ...]


# Priority is used only when scores are equal.
TOOL_PRIORITY = (
    "get_stock",
    "get_weather",
    "get_news",
    "find_nearby",
    "plan_trip",
    "web_search",
)

RULES: tuple[_Rule, ...] = (
    _Rule(
        tool="get_weather",
        strong_keywords=(
            "天气",
            "气温",
            "温度",
            "降雨",
            "下雨",
            "湿度",
            "体感",
            "几度",
            "冷不冷",
            "热不热",
            "有雨吗",
            "穿衣指数",
            "紫外线指数",
            "感冒指数",
            "洗车指数",
            "运动指数",
            "空气质量指数",
        ),
        weak_keywords=("风力", "空气质量", "穿什么", "会下雨", "晴天", "阴天"),
        patterns=(
            re.compile(r"(今天|明天|后天|本周|下周).*(天气|气温|温度|下雨)"),
            re.compile(r"([\u4e00-\u9fa5]{2,8})(市|县|区)?.*(天气|气温|下雨|几度)"),
        ),
    ),
    _Rule(
        tool="get_news",
        strong_keywords=("新闻", "头条", "快讯", "热点", "热搜", "资讯", "最新消息", "动态", "查下", "了解", "看看"),
        weak_keywords=("今日", "今天", "本周", "最近", "事件"),
        patterns=(
            re.compile(r"(今天|今日|最新|本周|最近).*(新闻|头条|快讯|热点|热搜)"),
            re.compile(r"(科技|AI|人工智能|财经|体育|国际|国内|教育|医药|旅游).*(新闻|快讯|头条)"),
            re.compile(r"(查下|了解|看看).*(发生了什么|热点|新闻|动态)"),
        ),
    ),
    _Rule(
        tool="get_stock",
        strong_keywords=(
            "股价",
            "股票",
            "行情",
            "涨跌",
            "k线",
            "开盘",
            "收盘",
            "市值",
            "大盘",
            "a股",
            "港股",
            "美股",
            "纳指",
            "道指",
            "上证",
            "深证",
        ),
        weak_keywords=("代码", "分时", "成交量", "盘前", "盘后", "走势"),
        patterns=(
            re.compile(r"\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b"),
            re.compile(r"(查|看|搜).*(股价|股票|行情|指数|大盘)"),
        ),
    ),
    _Rule(
        tool="find_nearby",
        strong_keywords=("附近", "周边", "最近的", "离我近", "哪儿有", "哪里有", "这里", "这附近"),
        weak_keywords=("餐厅", "饭店", "酒店", "咖啡", "医院", "药店", "停车场", "加油站", "商场", "推荐", "好吃的", "好玩的"),
        patterns=(
            re.compile(r"(附近|周边|最近|这里|这附近).*(餐厅|饭店|酒店|咖啡|医院|药店|停车场|加油站|商场|推荐|好吃的|好玩的)"),
            re.compile(r"(哪儿|哪里).*(有|能找到).*(附近|周边)?"),
            re.compile(r"(这里|这附近).*(有什么|推荐)"),
        ),
    ),
    _Rule(
        tool="plan_trip",
        strong_keywords=(
            "旅游",
            "旅行",
            "行程",
            "攻略",
            "自由行",
            "一日游",
            "两日游",
            "三日游",
            "四日游",
            "五日游",
            "路线规划",
            "怎么去",
            "规划",
            "游玩",
            "机票",
            "高铁",
            "路线",
            "玩",
        ),
        weak_keywords=("出行", "景点", "住哪", "预算", "交通", "去"),
        patterns=(
            re.compile(r"(去|到).*(怎么去|怎么走|路线|行程|玩)"),
            re.compile(r"(规划|安排|给).*(行程|旅游|旅行|\d+日游|路线)"),
            re.compile(r"(想|想去|去).*([\u4e00-\u9fa5]{2,8})(市|县|区)?.*(玩|旅游|旅行|行程)"),
        ),
    ),
    _Rule(
        tool="web_search",
        strong_keywords=(
            # 搜索行为
            "官网", "官方网站", "网址", "链接", "搜索", "搜一下", "查资料", "百度一下",
            # 人物查询
            "谁是", "成员", "演员", "明星", "歌手", "导演", "作家", "创始人",
            # 地点信息查询（非附近查询）
            "在哪", "位置", "地址", "具体位置", "坐标", "高度", "面积",
            # 体育赛事
            "比赛", "赛程", "赛事", "球队", "联赛", "世界杯", "奥运会",
            # 实体信息
            "乐队", "组合", "团队", "公司", "品牌",
            # 产品信息
            "价格", "多少钱", "怎么样", "评价", "参数", "配置",
            # 百科知识
            "什么是", "是什么", "介绍", "历史", "发展", "传说",
            # 教程文档
            "教程", "文档", "怎么用", "如何", "攻略",
            # 时事新闻（与 get_news 区分）
            "发布会", "最新消息",
            # 景点推荐
            "好玩的", "景点", "推荐",
        ),
        weak_keywords=("官网地址", "都有谁", "有哪些", "电影", "作品", "代表作"),
        patterns=(
            re.compile(r".*(官网|官方网站|网址|链接)$"),
            re.compile(r"(搜索|搜一下|查一下|查找).*(官网|资料|文档|教程|信息)?"),
            re.compile(r"(谁是|什么人|成员|演员|创始人).+"),
            re.compile(r".+(在哪|位置|地址|具体位置|高度|面积)"),
            re.compile(r".+(比赛|赛程|赛事|球队|世界杯|奥运会)"),
            re.compile(r".+(价格|多少钱|怎么样|评价)"),
            re.compile(r"(什么是|是什么).+"),
            re.compile(r".+(历史|发展|传说|由来)"),
            re.compile(r".+(教程|文档|攻略)"),
        ),
    ),
)


def route_query(query: str) -> RouteDecision:
    q = _normalize(query)
    scores, _reasons = _score_tools(q)

    best_tool, best_score = _pick_best(scores)
    # Avoid weak-keyword false positives (e.g. small talk accidentally routed to news).
    # 降低阈值从 3 到 2，让更多查询能路由到工具
    if best_score < 2:
        return RouteDecision("reply", _knowledge_probs(), tool_name=None)

    return RouteDecision("tool_call", _realtime_probs(best_tool), tool_name=best_tool)


def _normalize(q: str) -> str:
    return re.sub(r"\s+", "", q.strip().lower())


def _score_tools(q: str) -> tuple[dict[str, int], dict[str, list[str]]]:
    scores: dict[str, int] = {r.tool: 0 for r in RULES}
    reasons: dict[str, list[str]] = {r.tool: [] for r in RULES}

    # 排除闲聊（最高优先级）
    chitchat_signals = ("你好", "谢谢", "再见", "你是谁", "天气真好", "真不错", "太棒了")
    # Meta问题（关于助手自身）- 只保留这个修复
    meta_signals = ("你能做什么", "如何使用你", "你的功能")
    
    if any(k in q for k in chitchat_signals + meta_signals):
        # 闲聊/meta直接返回0分，不触发任何工具
        return scores, reasons

    for r in RULES:
        # strong keyword: +3
        for kw in r.strong_keywords:
            if kw in q:
                scores[r.tool] += 3
                reasons[r.tool].append(f"kw:{kw}")

        # weak keyword: +1
        for kw in r.weak_keywords:
            if kw in q:
                scores[r.tool] += 1
                reasons[r.tool].append(f"wk:{kw}")

        # regex pattern: +4
        for p in r.patterns:
            if p.search(q):
                scores[r.tool] += 4
                reasons[r.tool].append(f"re:{p.pattern}")

    # Disambiguation: weather life-index should not be routed to stock.
    weather_index_signals = ("穿衣指数", "紫外线指数", "感冒指数", "洗车指数", "运动指数", "空气质量指数")
    if any(k in q for k in weather_index_signals):
        scores["get_weather"] += 6
        scores["get_stock"] = max(0, scores["get_stock"] - 5)

    # Disambiguation: financial index signals strengthen stock route.
    stock_index_signals = ("上证指数", "深证指数", "创业板指数", "纳斯达克指数", "道琼斯指数", "恒生指数")
    if any(k in q for k in stock_index_signals):
        scores["get_stock"] += 6

    # Conflict resolution: nearby should beat generic search UNLESS it's a pure info query.
    # 排除：人物查询、体育赛事、纯地点信息查询（知名地标）
    info_query_signals = ("谁是", "成员", "演员", "明星", "比赛", "赛程", "球队", "乐队", "组合")
    landmark_query_signals = ("天文台", "博物馆", "纪念馆", "公园", "广场", "大厦", "塔", "寺", "庙", "教堂")
    is_info_query = any(k in q for k in info_query_signals)
    is_landmark_query = any(k in q for k in landmark_query_signals)
    
    if scores["find_nearby"] > 0 and scores["web_search"] > 0:
        if not is_info_query and not is_landmark_query:
            scores["find_nearby"] += 2
        else:
            # 信息查询或地标查询优先 web_search
            scores["web_search"] += 2

    # Conflict resolution: domain tools beat web search (except for info queries).
    for tool in ("get_weather", "get_news", "get_stock", "plan_trip"):
        if scores[tool] > 0 and scores["web_search"] > 0:
            if not is_info_query:
                scores[tool] += 1

    return scores, reasons


def _pick_best(scores: dict[str, int]) -> tuple[str, int]:
    best_tool = "web_search"
    best_score = -1

    for tool in TOOL_PRIORITY:
        sc = scores.get(tool, 0)
        if sc > best_score:
            best_tool = tool
            best_score = sc
    return best_tool, best_score


def _realtime_probs(tool_name: str) -> dict[str, float]:
    # Keep 7-class distribution but make realtime dominant.
    base = {"1": 0.02, "2": 0.03, "3": 0.03, "4": 0.02, "5": 0.04, "6": 0.84, "7": 0.02}
    # Slight lift for tool-call confidence marker by tool family (future use).
    if tool_name in {"get_weather", "get_news", "get_stock", "find_nearby", "plan_trip", "web_search"}:
        base["6"] = 0.88
        base["3"] = 0.02
    return base


def _knowledge_probs() -> dict[str, float]:
    return {"1": 0.05, "2": 0.25, "3": 0.45, "4": 0.1, "5": 0.05, "6": 0.05, "7": 0.05}
