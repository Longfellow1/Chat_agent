"""Dictionaries for location intent parsing."""

from __future__ import annotations

# 1. Landmark aliases (通俗名 -> 官方 POI)
# DEPRECATED: 已废弃，信任高德 NLU 能力
# 保留少量高频别名用于特殊情况
LANDMARK_ALIASES = {
    # 保留极少量高频别名（用户习惯 vs 官方名称差异大）
    "鸟巢": "国家体育场",
    "水立方": "国家游泳中心",
    # 其他地标直接使用原始文本，交给高德 NLU 处理
}

# 2. Brand to category mapping (品牌 -> 业态)
# Note: Keys should be in canonical form (Chinese preferred)
BRAND_CATEGORY_MAP = {
    # 便利店
    "711": "便利店",
    "7-11": "便利店",
    "全家": "便利店",
    "罗森": "便利店",
    "美宜佳": "便利店",
    "便利蜂": "便利店",
    # 快餐
    "肯德基": "快餐",
    "麦当劳": "快餐",
    "m记": "快餐",
    "汉堡王": "快餐",
    # 咖啡
    "星巴克": "咖啡厅",
    "瑞幸": "咖啡厅",
    "costa": "咖啡厅",
    # 餐厅
    "海底捞": "火锅",
    "呷哺呷哺": "火锅",
    "小肥羊": "火锅",
    # 可持续扩展
}

# Brand aliases (English/alternative names -> canonical Chinese name)
BRAND_ALIASES = {
    "kfc": "肯德基",
    "KFC": "肯德基",
    "麦当劳": "麦当劳",
    "m记": "麦当劳",
    "starbucks": "星巴克",
    "Starbucks": "星巴克",
    "luckin": "瑞幸",
    "Luckin": "瑞幸",
}

# 3. Sort keywords (自然语言 -> 排序策略)
SORT_KEYWORDS = {
    "最近": ("distance", "asc"),
    "离我最近": ("distance", "asc"),
    "最近的": ("distance", "asc"),
    "最好评": ("rating", "desc"),
    "评分最高": ("rating", "desc"),
    "好评": ("rating", "desc"),
    "人均最低": ("price", "asc"),
    "最便宜": ("price", "asc"),
    "便宜": ("price", "asc"),
    "人均最高": ("price", "desc"),
    "最贵": ("price", "desc"),
}

# 4. Constraint keywords (自然语言 -> 约束条件)
CONSTRAINT_KEYWORDS = {
    "24小时": {"open_24h": True},
    "24h": {"open_24h": True},
    "停车": {"has_parking": True},
    "停车位": {"has_parking": True},
    "wifi": {"has_wifi": True},
    "wi-fi": {"has_wifi": True},
    "外卖": {"has_delivery": True},
    "堂食": {"dine_in": True},
    "打包": {"takeout": True},
}

# 5. Category keywords (自然语言 -> 业态分类)
CATEGORY_KEYWORDS = {
    # 餐饮
    "餐厅": "餐厅",
    "饭店": "餐厅",
    "馆子": "餐厅",
    "吃饭": "餐厅",
    "美食": "餐厅",
    "好吃": "餐厅",
    "火锅": "火锅",
    "烤肉": "烤肉",
    "烧烤": "烧烤",
    "面馆": "面馆",
    "面条": "面馆",
    "快餐": "快餐",
    "西餐厅": "西餐厅",
    "西餐": "西餐厅",
    "中餐厅": "中餐厅",
    "中餐": "中餐厅",
    "日料": "日本料理",
    "韩餐": "韩国料理",
    "便利店": "便利店",
    "超市": "超市",
    # 服务
    "医院": "医院",
    "诊所": "诊所",
    "药店": "药店",
    "酒店": "酒店",
    "宾馆": "宾馆",
    "旅馆": "旅馆",
    "停车场": "停车场",
    "加油站": "加油站",
    "充电站": "充电站",
    # 娱乐
    "电影院": "电影院",
    "影院": "电影院",
    "ktv": "KTV",
    "KTV": "KTV",
    "K歌": "KTV",
    "卡拉OK": "KTV",
    "酒吧": "酒吧",
    "咖啡": "咖啡厅",
    "茶馆": "茶馆",
    "密室": "密室逃脱",
    "密室逃脱": "密室逃脱",
    "剧本杀": "剧本杀",
    "桌游": "桌游吧",
    # 购物
    "商场": "商场",
    "购物": "商场",
    "商店": "商店",
    "店铺": "商店",
    # 可持续扩展
}

# 6. Fuzzy category mapping (模糊词 -> 明确类别)
# 用于处理高德 NLU 无法理解的模糊表达
FUZZY_CATEGORY_MAP = {
    # 餐饮类
    "好吃的": "餐厅",
    "吃的": "餐厅",
    "吃什么": "餐厅",
    "吃饭": "餐厅",
    "美食": "餐厅",
    
    # 娱乐类（车载场景更倾向消费娱乐，而非名胜古迹）
    "好玩的": "娱乐",
    "玩的": "娱乐",
    "玩什么": "娱乐",
    
    # 购物类
    "逛街": "商场",
    "买东西": "商场",
    "买衣服": "商场",
    "购物": "商场",
    
    # 休闲类
    "喝酒": "酒吧",
    "唱歌": "KTV",
    "喝茶": "茶馆",
    "喝咖啡": "咖啡厅",
    "看电影": "电影院",
}


def resolve_landmark(name: str) -> str:
    """Resolve landmark alias to official POI name.
    
    DEPRECATED: 大部分地标不再归一化，直接使用原始文本。
    只保留极少量高频别名（用户习惯 vs 官方名称差异大）。
    """
    return LANDMARK_ALIASES.get(name, name)


def get_category_for_brand(brand: str) -> str:
    """Get category for a brand."""
    return BRAND_CATEGORY_MAP.get(brand, "")


def parse_sort_intent(query: str) -> tuple[str, str]:
    """Parse sort intent from query.
    
    Returns:
        (sort_by, sort_order) e.g. ("distance", "asc")
    """
    for keyword, (sort_by, order) in SORT_KEYWORDS.items():
        if keyword in query:
            return sort_by, order
    return "distance", "asc"


def parse_constraints(query: str) -> dict[str, bool]:
    """Parse constraint keywords from query."""
    constraints: dict[str, bool] = {}
    for keyword, constraint in CONSTRAINT_KEYWORDS.items():
        if keyword in query:
            constraints.update(constraint)
    return constraints


def parse_category(query: str) -> str:
    """Parse category from query.
    
    Returns most specific category match (longer keywords first).
    优先匹配模糊词（好吃的、好玩的等），然后匹配标准类别。
    """
    # 1. 先检查模糊词（按长度降序，优先匹配更长的）
    sorted_fuzzy = sorted(FUZZY_CATEGORY_MAP.keys(), key=len, reverse=True)
    for fuzzy_word in sorted_fuzzy:
        if fuzzy_word in query:
            return fuzzy_word  # 返回原始模糊词，后续在 to_tool_args() 中映射
    
    # 2. 再检查标准类别
    from .amap_type_codes import USER_CATEGORY_TO_AMAP_TYPE
    
    # Sort by keyword length descending to match longer/more specific terms first
    sorted_keywords = sorted(USER_CATEGORY_TO_AMAP_TYPE.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in query:
            return keyword
    return ""


def parse_brand(query: str) -> str:
    """Parse brand from query (case-insensitive).
    
    Returns canonical Chinese brand name if found.
    """
    q_lower = query.lower()
    
    # First check aliases (English/alternative names)
    for alias, canonical in BRAND_ALIASES.items():
        if alias.lower() in q_lower:
            return canonical
    
    # Then check canonical brands
    for brand in BRAND_CATEGORY_MAP.keys():
        if brand.lower() in q_lower:
            return brand
    
    return ""


def normalize_fuzzy_category(keyword: str) -> str:
    """Normalize fuzzy category keywords to concrete categories.
    
    高德 NLU 对某些模糊词理解不好（如"好吃的"、"好玩的"），
    需要在 Parser 层做一次映射，转换为高德能理解的明确类别。
    
    Args:
        keyword: 原始关键词（可能包含模糊表达）
        
    Returns:
        标准化后的关键词（模糊词被替换为明确类别）
        
    Examples:
        "好吃的" -> "餐厅"
        "好玩的" -> "景点"
        "火锅" -> "火锅" (不变)
    """
    # 按长度降序排序，优先匹配更长的模糊词（避免"好吃的"被"吃的"覆盖）
    sorted_fuzzy = sorted(FUZZY_CATEGORY_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    
    for fuzzy_word, concrete_category in sorted_fuzzy:
        if fuzzy_word in keyword:
            # 替换模糊词为明确类别
            return keyword.replace(fuzzy_word, concrete_category)
    
    return keyword
