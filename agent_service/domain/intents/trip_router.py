"""
Trip Planning Intent Router

处理 plan_trip 意图识别和参数提取
"""

import re
from typing import Dict, Optional, Tuple


# 行程规划信号词
TRIP_SIGNALS = {
    "planning": ["规划", "行程", "安排", "计划"],
    "planning_weak": ["攻略"],  # 弱信号词，需要和天数或旅游词共现
    "travel": ["旅游", "玩", "游", "旅行", "出游"],
    "days": ["日游", "天", "两天", "三天", "几天"],
    "driving": ["自驾", "开车", "驾车", "自己开车"],
}

# 偏好信号词（M5.2）
PREFERENCE_SIGNALS = {
    "food": ["美食", "吃", "餐厅", "小吃", "吃吃吃", "品尝", "美味", "特色菜"],
    "entertainment": ["娱乐", "玩乐", "酒吧", "夜生活", "KTV", "夜店", "玩玩玩"],
    "culture": ["文化", "博物馆", "历史", "古迹", "寺庙", "遗址", "人文"],
    "nature": ["自然", "风景", "山", "湖", "公园", "户外", "爬山", "徒步"],
    "shopping": ["购物", "商场", "逛街", "买买买", "奢侈品", "血拼"],
    "relax": ["休闲", "放松", "茶馆", "SPA", "温泉", "慢游", "悠闲"],
}

# 排除模式（不应该路由到plan_trip）
EXCLUDE_PATTERNS = [
    r"(到|去).+(怎么走|路线|导航|怎么去)",  # 导航意图
    r"(有什么|哪里有|推荐).+(景点|餐厅|酒店|地方)",  # find_nearby意图
    r"(天气|气温|下雨)",  # get_weather意图
    r"(新闻|热点|头条)",  # get_news意图
    r"(打开|启动|功能|在哪里)",  # 操作指令
]

# 城市名称模式（简化版，实际应该更完整）
CITY_PATTERN = r"(北京|上海|广州|深圳|杭州|成都|重庆|西安|南京|武汉|苏州|天津|青岛|长沙|郑州|厦门|济南|哈尔滨|沈阳|大连|昆明|福州|无锡|合肥|南昌|贵阳|南宁|兰州|石家庄|太原|乌鲁木齐|拉萨|银川|西宁|呼和浩特|海口|三亚|桂林|丽江|大理|黄山|张家界|九寨沟|峨眉山|泰山|华山|庐山|武夷山|鼓浪屿|凤凰古城|乌镇|周庄|同里|西塘|婺源|宏村|平遥|丽水|台州|温州|宁波|绍兴|嘉兴|湖州|金华|衢州|舟山|丽水|扬州|镇江|常州|徐州|盐城|淮安|连云港|宿迁|泰州|南通|芜湖|蚌埠|淮南|马鞍山|淮北|铜陵|安庆|黄山|滁州|阜阳|宿州|六安|亳州|池州|宣城)"


def is_trip_intent(query: str) -> bool:
    """
    判断是否是行程规划意图
    
    Args:
        query: 用户查询
        
    Returns:
        是否是行程规划意图
    """
    # 1. 检查排除模式
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, query):
            return False
    
    # 2. 检查是否包含行程规划信号词
    planning_score = sum(1 for kw in TRIP_SIGNALS["planning"] if kw in query)
    planning_weak_score = sum(1 for kw in TRIP_SIGNALS["planning_weak"] if kw in query)
    travel_score = sum(1 for kw in TRIP_SIGNALS["travel"] if kw in query)
    driving_score = sum(1 for kw in TRIP_SIGNALS["driving"] if kw in query)
    
    # 3. 检查是否包含目的地（城市名）
    has_destination = bool(re.search(CITY_PATTERN, query))
    
    # 4. 检查是否包含天数
    days_score = sum(1 for kw in TRIP_SIGNALS["days"] if kw in query)
    
    # 5. 检查是否包含偏好（M5.2）
    preference_score = sum(
        1 for pref_keywords in PREFERENCE_SIGNALS.values()
        for kw in pref_keywords if kw in query
    )
    
    # 如果有明确的规划词 + 目的地，则是行程规划意图
    if planning_score > 0 and has_destination:
        return True
    
    # 如果有弱规划词（如"攻略"），必须和天数或旅游词共现
    if planning_weak_score > 0 and has_destination:
        if days_score > 0 or travel_score > 0:
            return True
    
    # 如果有旅游词 + 目的地 + 天数，则是行程规划意图
    if travel_score > 0 and has_destination and days_score > 0:
        return True
    
    # 新增：如果有自驾/驾车 + 目的地 + 旅游词，则是行程规划意图
    # 覆盖"驾车杭州旅游"这类case
    if driving_score > 0 and has_destination and travel_score > 0:
        return True
    
    # 新增：如果有自驾/驾车 + 目的地 + 天数，则是行程规划意图
    # 覆盖"自驾南京3天"这类case
    if driving_score > 0 and has_destination and days_score > 0:
        return True
    
    # M5.2新增：如果有偏好 + 目的地 + 天数，则是行程规划意图
    # 覆盖"成都吃货之旅2天"、"西安历史古迹2天"这类case
    if preference_score > 0 and has_destination and days_score > 0:
        return True
    
    return False


def extract_trip_params(query: str) -> Dict[str, Optional[str | int | list]]:
    """
    提取行程规划参数
    
    Args:
        query: 用户查询
        
    Returns:
        参数字典 {destination, days, travel_mode, preferences}
    """
    params = {
        "destination": None,
        "days": 2,  # 默认2天
        "travel_mode": "transit",  # 默认公共交通
        "preferences": [],  # M5.2: 用户偏好列表
    }
    
    # 1. 提取目的地
    city_match = re.search(CITY_PATTERN, query)
    if city_match:
        params["destination"] = city_match.group(1)
    
    # 2. 提取天数
    # 匹配 "X日游"、"X天"、"两天"、"三天"、"一日游" 等
    days_patterns = [
        (r"一日游", lambda m: 1),
        (r"(\d+)日游", lambda m: int(m.group(1))),
        (r"(\d+)天", lambda m: int(m.group(1))),
        (r"一天|1天", lambda m: 1),
        (r"两天|2天", lambda m: 2),
        (r"三天|3天", lambda m: 3),
        (r"四天|4天", lambda m: 4),
        (r"五天|5天", lambda m: 5),
    ]
    
    for pattern, extractor in days_patterns:
        match = re.search(pattern, query)
        if match:
            params["days"] = extractor(match)
            break
    
    # 3. 提取出行方式
    driving_score = sum(1 for kw in TRIP_SIGNALS["driving"] if kw in query)
    if driving_score > 0:
        params["travel_mode"] = "driving"
    
    # 4. 提取偏好（M5.2）
    preferences = []
    for pref_type, keywords in PREFERENCE_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in query)
        if score > 0:
            preferences.append(pref_type)
    
    # M5.4: 偏好数量限制（最多2个）
    if len(preferences) > 2:
        preferences = preferences[:2]
    
    params["preferences"] = preferences
    
    return params


def route_trip_intent(query: str) -> Tuple[bool, Dict[str, Optional[str | int | list]], str]:
    """
    路由行程规划意图
    
    Args:
        query: 用户查询
        
    Returns:
        (is_trip, params, reason)
        - is_trip: 是否是行程规划意图
        - params: 提取的参数
        - reason: 判断原因
    """
    # 1. 检查排除模式
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, query):
            return False, {}, f"匹配排除模式: {pattern}"
    
    # 2. 检查是否是行程规划意图
    if not is_trip_intent(query):
        return False, {}, "不包含行程规划信号词或目的地"
    
    # 3. 提取参数
    params = extract_trip_params(query)
    
    # 4. 检查参数完整性
    if not params["destination"]:
        return False, params, "缺少目的地信息"
    
    return True, params, "匹配行程规划意图"


def get_trip_routing_debug_info(query: str) -> Dict:
    """
    获取路由调试信息
    
    Args:
        query: 用户查询
        
    Returns:
        调试信息字典
    """
    is_trip, params, reason = route_trip_intent(query)
    
    # 计算信号词得分
    planning_score = sum(1 for kw in TRIP_SIGNALS["planning"] if kw in query)
    travel_score = sum(1 for kw in TRIP_SIGNALS["travel"] if kw in query)
    days_score = sum(1 for kw in TRIP_SIGNALS["days"] if kw in query)
    driving_score = sum(1 for kw in TRIP_SIGNALS["driving"] if kw in query)
    
    # 计算偏好得分（M5.2）
    preference_scores = {}
    for pref_type, keywords in PREFERENCE_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in query)
        if score > 0:
            preference_scores[pref_type] = score
    
    # 检查排除模式
    excluded_patterns = []
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, query):
            excluded_patterns.append(pattern)
    
    return {
        "query": query,
        "is_trip_intent": is_trip,
        "params": params,
        "reason": reason,
        "scores": {
            "planning": planning_score,
            "travel": travel_score,
            "days": days_score,
            "driving": driving_score,
            "preferences": preference_scores,
        },
        "excluded_patterns": excluded_patterns,
    }
