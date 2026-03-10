"""
Web Search Intent Router

处理 web_search 与其他工具的冲突，防止误触发
"""

import re
from typing import Any


# 工具规则定义
TOOL_RULES = {
    "web_search": {
        # 强关键词：明确指向搜索行为（独立触发）
        "strong_keywords": (
            "搜一下", "百度一下", "谷歌一下", "搜索",
            "官网", "官方网站", "网址", "链接",
            "查资料", "查一下资料", "了解一下",
        ),
        "strong_score": 3,
        
        # 弱关键词：辅助信号（需要组合判断）
        "weak_keywords": (
            "最新", "价格", "怎么样", "评价",
            "是什么", "介绍", "文档", "教程",
        ),
        "weak_score": 1,
        
        # 排除模式：优先级更高（防止误触发）
        "exclude_patterns": (
            r"(天气|气温|下雨|空气|湿度|风力|降水)",  # 天气类
            r"(股票|股价|涨跌|行情|指数)",            # 股票类
            r"(附近|周边|导航|地点|餐厅|酒店)",      # 地点类
            r"(新闻|热点|头条|资讯)",                # 新闻类
        ),
    },
    "get_weather": {
        "strong_keywords": ("天气", "气温", "下雨", "空气", "湿度", "风力"),
        "strong_score": 3,
        "weak_keywords": ("明天", "今天", "后天", "预报"),
        "weak_score": 1,
    },
    "get_stock": {
        "strong_keywords": ("股票", "股价", "涨跌", "行情", "指数"),
        "strong_score": 3,
        "weak_keywords": ("价格", "最新"),
        "weak_score": 1,
    },
    "get_news": {
        "strong_keywords": ("新闻", "热点", "头条", "资讯"),
        "strong_score": 3,
        "weak_keywords": ("最新", "今日"),
        "weak_score": 1,
    },
    "find_nearby": {
        "strong_keywords": ("附近", "周边", "导航", "地点", "餐厅", "酒店"),
        "strong_score": 3,
        "weak_keywords": ("推荐", "有没有"),
        "weak_score": 1,
    },
}


def route_tool(query: str, candidate_tools: list[str] | None = None) -> str:
    """
    路由工具选择
    
    Args:
        query: 用户查询
        candidate_tools: 候选工具列表（如果为None，则考虑所有工具）
        
    Returns:
        选中的工具名称
    """
    if candidate_tools is None:
        candidate_tools = list(TOOL_RULES.keys())
    
    scores = {}
    
    # 1. 检查排除模式（最高优先级）
    for tool in candidate_tools:
        rules = TOOL_RULES.get(tool, {})
        for pattern in rules.get("exclude_patterns", []):
            if re.search(pattern, query):
                scores[tool] = -999  # 排除
    
    # 2. 计算强关键词分数
    for tool in candidate_tools:
        if scores.get(tool, 0) < 0:  # 已被排除
            continue
        rules = TOOL_RULES.get(tool, {})
        for kw in rules.get("strong_keywords", []):
            if kw in query:
                scores[tool] = scores.get(tool, 0) + rules["strong_score"]
    
    # 3. 计算弱关键词分数（仅当无强关键词时）
    for tool in candidate_tools:
        if scores.get(tool, 0) < 0:  # 已被排除
            continue
        rules = TOOL_RULES.get(tool, {})
        if scores.get(tool, 0) < rules["strong_score"]:
            for kw in rules.get("weak_keywords", []):
                if kw in query:
                    scores[tool] = scores.get(tool, 0) + rules["weak_score"]
    
    # 4. 冲突解决：垂直工具优先
    if scores.get("web_search", 0) > 0:
        for tool in ("get_weather", "get_news", "get_stock", "find_nearby", "plan_trip"):
            if scores.get(tool, 0) > 0:
                scores[tool] += 1  # 垂直工具加分
    
    # 5. 返回最高分工具
    valid_scores = {k: v for k, v in scores.items() if v >= 0}
    if not valid_scores:
        return "web_search"  # 默认降级到 web_search
    
    return max(valid_scores, key=valid_scores.get)


def should_route_to_web_search(query: str, original_tool: str) -> bool:
    """
    判断是否应该路由到 web_search
    
    Args:
        query: 用户查询
        original_tool: 原始选择的工具
        
    Returns:
        是否应该路由到 web_search
    """
    # 如果原始工具已经是 web_search，不需要再判断
    if original_tool == "web_search":
        return True
    
    # 检查是否有强烈的 web_search 信号
    rules = TOOL_RULES.get("web_search", {})
    strong_count = sum(1 for kw in rules.get("strong_keywords", []) if kw in query)
    
    # 如果有多个强关键词，应该路由到 web_search
    if strong_count >= 2:
        return True
    
    # 检查排除模式
    for pattern in rules.get("exclude_patterns", []):
        if re.search(pattern, query):
            return False
    
    return False


def get_routing_debug_info(query: str) -> dict[str, Any]:
    """
    获取路由调试信息
    
    Args:
        query: 用户查询
        
    Returns:
        调试信息字典
    """
    scores = {}
    
    for tool in TOOL_RULES.keys():
        rules = TOOL_RULES[tool]
        score = 0
        
        # 检查排除模式
        excluded = False
        for pattern in rules.get("exclude_patterns", []):
            if re.search(pattern, query):
                excluded = True
                break
        
        if excluded:
            score = -999
        else:
            # 强关键词
            for kw in rules.get("strong_keywords", []):
                if kw in query:
                    score += rules["strong_score"]
            
            # 弱关键词
            if score < rules["strong_score"]:
                for kw in rules.get("weak_keywords", []):
                    if kw in query:
                        score += rules["weak_score"]
        
        scores[tool] = score
    
    # 冲突解决
    if scores.get("web_search", 0) > 0:
        for tool in ("get_weather", "get_news", "get_stock", "find_nearby", "plan_trip"):
            if scores.get(tool, 0) > 0:
                scores[tool] += 1
    
    selected = max((k for k, v in scores.items() if v >= 0), key=lambda k: scores[k], default="web_search")
    
    return {
        "query": query,
        "scores": scores,
        "selected_tool": selected,
    }
