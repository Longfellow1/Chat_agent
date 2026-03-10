from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolPlan:
    tool_name: str
    tool_args: dict[str, Any] = field(default_factory=dict)
    missing_slots: list[str] = field(default_factory=list)
    extract_source: str = "rule"


def build_tool_plan(query: str, tool_name: str) -> ToolPlan:
    if tool_name == "get_weather":
        city = extract_city(query)
        if not city:
            return ToolPlan(tool_name=tool_name, missing_slots=["city"])
        return ToolPlan(tool_name=tool_name, tool_args={"city": city})

    if tool_name == "get_news":
        topic = extract_topic(query, default="今日热点")
        return ToolPlan(tool_name=tool_name, tool_args={"topic": topic})

    if tool_name == "get_stock":
        target = extract_topic(query, default="上证指数")
        return ToolPlan(tool_name=tool_name, tool_args={"target": target})

    if tool_name == "plan_trip":
        city = extract_city(query)
        if not city:
            return ToolPlan(tool_name=tool_name, missing_slots=["destination"])
        return ToolPlan(tool_name=tool_name, tool_args={"destination": city})

    if tool_name == "find_nearby":
        city = extract_city(query)
        keyword = extract_nearby_keyword(query, city=city, default="餐厅")
        args = {"keyword": keyword}
        if city:
            args["city"] = city
        return ToolPlan(tool_name=tool_name, tool_args=args)

    if tool_name == "web_search":
        # 使用 query_preprocessor 进行查询优化
        try:
            from domain.tools.query_preprocessor import preprocess_web_search_query
        except ImportError:
            from agent_service.domain.tools.query_preprocessor import preprocess_web_search_query
        preprocessed = preprocess_web_search_query(query)
        optimized_query = preprocessed["normalized_query"]
        
        # 识别实体类型
        entity_type = _identify_entity_type(query)
        
        args = {"query": optimized_query}
        if entity_type:
            args["entity_type"] = entity_type
        
        return ToolPlan(tool_name=tool_name, tool_args=args)

    return ToolPlan(tool_name=tool_name)


def extract_rule_tool_args(query: str, tool_name: str) -> dict[str, Any]:
    q = query.strip()
    if tool_name == "get_weather":
        city = extract_city(q)
        return {"city": city} if city else {}
    if tool_name == "get_news":
        return {"topic": extract_topic(q, default="今日热点")}
    if tool_name == "get_stock":
        target = extract_stock_target(q)
        return {"target": target} if target else {}
    if tool_name == "plan_trip":
        city = extract_city(q)
        days = extract_days(q)
        out: dict[str, Any] = {}
        if city:
            out["destination"] = city
        if days:
            out["days"] = str(days)
        return out
    if tool_name == "find_nearby":
        city = extract_city(q)
        keyword = extract_nearby_keyword(q, city=city, default="餐厅")
        out = {"keyword": keyword}
        if city:
            out["city"] = city
        return out
    if tool_name == "web_search":
        # 使用 query_preprocessor 进行查询优化
        try:
            from domain.tools.query_preprocessor import preprocess_web_search_query
        except ImportError:
            from agent_service.domain.tools.query_preprocessor import preprocess_web_search_query
        preprocessed = preprocess_web_search_query(q)
        optimized_query = preprocessed["normalized_query"]
        
        # 识别实体类型
        entity_type = _identify_entity_type(q)
        
        result = {"query": optimized_query}
        if entity_type:
            result["entity_type"] = entity_type
        
        return result
    return {}


def normalize_tool_args(tool_name: str, tool_args: dict[str, Any], raw_query: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if tool_name == "get_weather":
        city = _as_text(tool_args.get("city"))
        if city in {"当前城市", "所在城市", "本地", "这里", "本地城市"}:
            city = ""
        if city:
            out["city"] = city
        return out
    if tool_name == "get_news":
        topic = _as_text(tool_args.get("topic")) or extract_topic(raw_query, default="今日热点")
        out["topic"] = topic
        return out
    if tool_name == "get_stock":
        target = _as_text(tool_args.get("target")) or extract_stock_target(raw_query) or extract_topic(raw_query, default="上证指数")
        out["target"] = target
        return out
    if tool_name == "find_nearby":
        city = _as_text(tool_args.get("city"))
        keyword = _as_text(tool_args.get("keyword")) or extract_nearby_keyword(raw_query, city=city, default="餐厅")
        out["keyword"] = keyword
        if city:
            out["city"] = city
        return out
    if tool_name == "plan_trip":
        city = _as_text(tool_args.get("destination")) or extract_city(raw_query)
        if city in {"当前城市", "所在城市", "本地", "这里", "本地城市"}:
            city = ""
        days = _as_text(tool_args.get("days")) or str(extract_days(raw_query) or "")
        if city:
            out["destination"] = city
        if days:
            out["days"] = days
        return out
    if tool_name == "web_search":
        query = _as_text(tool_args.get("query")) or raw_query
        out["query"] = query
        return out
    return out


def required_slots(tool_name: str) -> tuple[str, ...]:
    if tool_name == "get_weather":
        return ("city",)
    if tool_name == "plan_trip":
        return ("destination",)
    return ()


def extract_city(query: str) -> str | None:
    """Extract city from query with improved robustness.
    
    Handles cases like:
    - "北京最近天气" → "北京"
    - "帮我查一下北京天气" → "北京"
    - "明天上海下雨吗" → "上海"
    """
    q = query.strip()

    # Pattern 1: 城市+市/县/区
    m = re.search(r"([\u4e00-\u9fa5]{2,8})(市|县|区)", q)
    if m:
        return f"{m.group(1)}{m.group(2)}"

    # Pattern 2: Known cities (expanded list)
    known = (
        "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "成都", "重庆", "武汉", 
        "郑州", "西安", "天津", "长沙", "青岛", "大连", "沈阳", "哈尔滨", "济南", "合肥",
        "福州", "厦门", "南昌", "长春", "石家庄", "太原", "呼和浩特", "兰州", "银川",
        "西宁", "乌鲁木齐", "拉萨", "昆明", "贵阳", "海口", "三亚", "南宁", "桂林"
    )
    for c in known:
        if c in q:
            return c
    
    # Pattern 3: First word (if it looks like a city)
    # But skip common time/weather words
    parts = re.split(r"[，,。！？? ]+", q)
    if parts:
        first = parts[0].strip()
        # Remove common prefixes
        first = re.sub(r"^(帮我|请|查询|查一下|查查|看看|想看|我要)", "", first)
        first = first.strip()
        
        if 2 <= len(first) <= 5 and re.fullmatch(r"[\u4e00-\u9fa5]+", first):
            blocked = {
                "今天", "明天", "后天", "现在", "最近", "下周", "周末",
                "天气", "新闻", "股票", "附近", "周边", "这里", "那里"
            }
            if first not in blocked:
                return first
    
    return None


def extract_days(query: str) -> int | None:
    q = query.strip()
    m = re.search(r"(\d{1,2})\s*天", q)
    if m:
        try:
            return max(1, int(m.group(1)))
        except Exception:
            return None
    cn = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    m2 = re.search(r"([一二两三四五六七八九十])天", q)
    if m2:
        return cn.get(m2.group(1))
    return None


def extract_topic(query: str, default: str) -> str:
    q = query.strip()
    q = re.sub(r"(帮我|请|查询|查一下|查查|看看|想看|我要看)", "", q)
    q = re.sub(r"\s+", "", q)
    q = q.strip("，,。！？? ")
    return q or default


def extract_stock_target(query: str) -> str | None:
    q = query.strip()
    aliases = {
        "京东": "JD",
        "贵州茅台": "600519.SS",
        "茅台": "600519.SS",
        "上证指数": "000001.SS",
        "上证": "000001.SS",
        "深证成指": "399001.SZ",
        "深证": "399001.SZ",
    }
    for k, v in aliases.items():
        if k in q:
            return v

    m = re.search(r"\b([A-Z]{1,5}(?:\.[A-Z]{1,3})?)\b", q.upper())
    if m:
        return m.group(1)
    m2 = re.search(r"\b(\d{6})\b", q)
    if m2:
        return f"{m2.group(1)}.SS"
    if any(k in q for k in ("股价", "股票", "行情", "涨跌", "指数")):
        return extract_topic(q, default="上证指数")
    return None


def extract_nearby_keyword(query: str, city: str | None, default: str) -> str:
    q = query.strip()
    if city:
        q = q.replace(city, "")
    # Normalize nearby intent words first.
    food_signals = ("好吃", "美食", "吃什么", "餐馆", "馆子", "饭店", "小吃")
    if any(s in q for s in food_signals):
        for s in food_signals:
            q = q.replace(s, " ")
        # Keep explicit place anchor in query and force food category keyword.
        q = q.strip()
        anchor = re.sub(r"(都有|都有什么|有什么|什么|哪里|哪儿|推荐|一下|一下子|可以|吗|呢|吧|都|的)", " ", q)
        anchor = re.sub(r"[，,。！？?\\s]+", " ", anchor).strip()
        if anchor:
            return f"{anchor} 餐厅"
        return "餐厅"

    # Convenience-store style queries: "鸟巢周边 最近的711是哪一家"
    conv_signals = ("711", "7-11", "便利店", "全家", "罗森", "美宜佳")
    if any(s.lower() in q.lower() for s in conv_signals):
        anchor = q
        for w in (
            "附近",
            "周边",
            "最近",
            "离我最近",
            "哪一家",
            "哪家",
            "是哪家",
            "是哪一家",
            "在哪里",
            "在什么地方",
            "有吗",
            "有没有",
            "的",
            "请",
            "帮我",
            "找",
            "查一下",
            "查查",
        ):
            anchor = anchor.replace(w, " ")
        # Keep main place anchor and convenience category.
        anchor = re.sub(r"(711|7-11|便利店|全家|罗森|美宜佳)", " ", anchor, flags=re.IGNORECASE)
        anchor = re.sub(r"[，,。！？?\\s]+", " ", anchor).strip()
        brand = "711" if re.search(r"(711|7-11)", q, flags=re.IGNORECASE) else "便利店"
        return f"{anchor} {brand}".strip()

    for w in ("附近", "周边", "最近", "查一下", "查查", "帮我", "搜索", "找", "有没有", "推荐", "的", "请", "都有什么", "有什么"):
        q = q.replace(w, " ")
    q = re.sub(r"[，,。！？?\\s]+", " ", q).strip()
    return q or default


def _as_text(v: object) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _identify_entity_type(query: str) -> str | None:
    """
    识别查询中的实体类型
    
    Args:
        query: 用户查询
        
    Returns:
        实体类型：person（人物）、concept（概念）、product（产品）、event（事件）或 None
    """
    q = query.lower()
    
    # 人物类
    if any(k in q for k in ["谁是", "什么人", "演员", "明星", "歌手", "导演", "作家"]):
        return "person"
    
    # 概念类
    if any(k in q for k in ["什么是", "是什么", "定义", "含义", "解释"]):
        return "concept"
    
    # 产品类
    if any(k in q for k in ["价格", "多少钱", "售价", "报价", "购买", "怎么买"]):
        return "product"
    
    # 事件类
    if any(k in q for k in ["什么时候", "几点", "日期", "时间", "发生", "举办"]):
        return "event"
    
    return None
