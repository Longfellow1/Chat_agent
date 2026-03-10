"""Location intent parser using regex-based field extraction for Amap MCP."""

from __future__ import annotations

import re
from typing import Any

from .intent import LocationIntent, AnchorType, SortBy
from .dictionaries import (
    LANDMARK_ALIASES,
    BRAND_CATEGORY_MAP,
    SORT_KEYWORDS,
    parse_brand,
    parse_category,
)


def parse_location_intent(query: str) -> LocationIntent:
    """Parse location intent from query using regex-based extraction.

    Extracts structured fields that map directly to Amap MCP parameters:
    - city: for 'city' parameter
    - anchor_poi: for first-hop location search
    - brand/category: for 'keywords' parameter

    Args:
        query: User query (e.g., "北京市的鸟巢周边，最近的711是哪一家")

    Returns:
        LocationIntent with extracted fields

    Example:
        Input: "北京市的鸟巢周边，最近的711是哪一家"
        Output: LocationIntent(
            city="北京市",
            anchor_poi="国家体育场",  # resolved from "鸟巢"
            brand="711",
            category="便利店",
            sort_by=SortBy.DISTANCE
        )
    """
    intent = LocationIntent(raw_query=query)

    # 1. Extract city (城市) with anchor conflict detection
    intent.city = _extract_city(query)

    # 2. Extract anchor POI FIRST (pass city to avoid re-extraction conflicts)
    intent.anchor_poi = _extract_anchor_poi(query, intent.city)
    if intent.anchor_poi:
        intent.anchor_type = AnchorType.LANDMARK

    # 3. Extract district (区) - only if anchor not found
    if not intent.anchor_poi:
        intent.district = _extract_district(query)
        if intent.district:
            intent.anchor_poi = intent.district
            intent.anchor_type = AnchorType.POI

    # 4. Extract street (街道) - optional
    intent.street = _extract_street(query)

    # 5. Extract brand (品牌)
    intent.brand = parse_brand(query)

    # 6. Extract category (服务类型) - remove anchor from query first to avoid conflicts
    # Example: "杭州武林广场的泰餐" -> remove "武林广场" before parsing category
    query_for_category = query.replace(intent.anchor_poi, "") if intent.anchor_poi else query
    intent.category = parse_category(query_for_category)

    # If brand found, infer category
    if intent.brand and not intent.category:
        intent.category = BRAND_CATEGORY_MAP.get(intent.brand, "")

    # 7. Extract sort intent (排序)
    sort_by, sort_order = _extract_sort_intent(query)
    intent.sort_by = SortBy(sort_by)
    intent.sort_order = sort_order

    # 8. Extract constraints (约束条件)
    intent.constraints = _extract_constraints(query)

    # 9. Set confidence
    intent.confidence = _calculate_confidence(intent)

    return intent


def _extract_city(query: str) -> str:
    """Extract city using complete city whitelist with anchor conflict detection.

    Strategy:
    1. Use complete city whitelist (~300 cities from workflow node 100138)
    2. For each city match, check if followed by POI suffix (路/街/道/广场)
    3. If yes, skip (it's part of anchor like "南京路", "中山路")

    Examples:
    - "上海南京路的商场" -> "上海" (not "南京", because "南京路" is anchor)
    - "厦门中山路的甜品店" -> "厦门" (not "中山", because "中山路" is anchor)
    """
    # POI suffixes that indicate the city is part of an anchor
    POI_SUFFIXES = {'路', '街', '道', '广场', '大街', '大道', '步行街', '商业街'}

    # Complete city whitelist from workflow (all_cities set)
    ALL_CITIES = {
        "北京", "上海", "天津", "重庆", "香港", "澳门", "台北", "高雄",
        "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮",
        "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水",
        "太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁",
        "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布", "兴安", "锡林郭勒", "阿拉善",
        "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛",
        "长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边",
        "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭",
        "南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁",
        "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水",
        "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城",
        "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德",
        "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶",
        "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽",
        "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店",
        "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施", "仙桃", "潜江", "天门", "神农架",
        "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西",
        "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左",
        "海口", "三亚", "三沙", "儋州",
        "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝", "甘孜", "凉山",
        "贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南", "黔东南", "黔南",
        "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄", "红河", "文山", "西双版纳", "大理", "德宏", "怒江", "迪庆",
        "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里",
        "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛",
        "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏", "甘南",
        "西宁", "海东", "海北", "黄南", "海南", "果洛", "玉树", "海西",
        "银川", "石嘴山", "吴忠", "固原", "中卫",
        "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉", "博尔塔拉", "巴音郭楞", "阿克苏", "克孜勒苏", "喀什", "和田", "伊犁", "塔城", "阿勒泰"
    }

    # Remove common prefix words that might interfere
    q = query
    prefix_words = ["请问", "帮我", "查一下", "查查", "找一下", "找找"]
    for prefix in prefix_words:
        q = q.replace(prefix, "")

    # Try each city with conflict detection
    # Sort by length desc, then find the first match at position 0 (start of query)
    best_city = ""
    best_pos = len(q) + 1
    
    for city in sorted(ALL_CITIES, key=len, reverse=True):
        pos = q.find(city)
        if pos == -1:
            continue

        # Check if city is followed by POI suffix (anchor conflict detection)
        end = pos + len(city)
        if end < len(q) and q[end] in POI_SUFFIXES:
            continue  # This city is part of an anchor like "南京路", skip it

        # Prefer city at earlier position (closer to start of query)
        if pos < best_pos:
            best_city = city
            best_pos = pos
            # If found at position 0, return immediately
            if pos == 0:
                return city
    
    if best_city:
        return best_city

    # Fallback: try regex for cities with "市" suffix
    match = re.search(r"([\u4e00-\u9fa5]{2,4})市", q)
    if match:
        return f"{match.group(1)}市"

    return ""


def _extract_district(query: str) -> str:
    """Extract district using regex pattern.
    
    Pattern: ([\u4e00-\u9fa5]{2,6})区
    Examples: 朝阳区, 浦东新区, 黄浦区
    
    Also handles: 北京朝阳 -> 朝阳区
    
    Note: This function is only called when anchor_poi is not found (see parse_location_intent).
    Therefore, no anchor conflict detection is needed here. The execution order ensures that
    landmarks like "静安寺" are extracted as anchor before "静安" is extracted as district.
    """
    # Remove city first to avoid matching "北京市朝阳区" as district
    q = query
    q = re.sub(r"[\u4e00-\u9fa5]{2,4}市", "", q)
    
    # Now extract district with "区" suffix
    match = re.search(r"([\u4e00-\u9fa5]{2,6})区", q)
    if match:
        return f"{match.group(1)}区"
    
    # Handle known districts without "区" suffix (e.g., "北京朝阳")
    known_districts = {
        "朝阳": "朝阳区",
        "海淀": "海淀区",
        "东城": "东城区",
        "西城": "西城区",
        "丰台": "丰台区",
        "石景山": "石景山区",
        "浦东": "浦东新区",
        "浦西": "浦西区",
        "黄浦": "黄浦区",
        "静安": "静安区",
        "徐汇": "徐汇区",
        "长宁": "长宁区",
        "普陀": "普陀区",
        "虹口": "虹口区",
        "杨浦": "杨浦区",
        "南山": "南山区",
        "福田": "福田区",
        "罗湖": "罗湖区",
    }
    
    for district_name, district_full in known_districts.items():
        if district_name in q:
            return district_full
    
    return ""


def _extract_street(query: str) -> str:
    """Extract street using regex pattern.
    
    Pattern: ([\u4e00-\u9fa5]{2,8})(街|路|道)
    Examples: 中关村大街, 长安路, 建国道
    """
    match = re.search(r"([\u4e00-\u9fa5]{2,8})(街|路|道)", query)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return ""


def _extract_anchor_poi(query: str, extracted_city: str = "") -> str:
    """Extract anchor POI (landmark/location) using positive pattern matching.

    Strategy (learned from workflow node 1560882):
    1. Check known landmarks from dictionary (ONLY for high-frequency aliases like "鸟巢")
    2. Check 2-4 char landmarks with special suffixes (寺|口|谷|碑|单|庙|里|屯|井)
    3. Primary: Extract "XX(附近|周边|旁边|周围|一带)" pattern
    4. Fallback: Extract POI suffix patterns (路|街|广场|公园|景区|大厦|中心|站)
    5. Return empty string (let caller fallback to district)

    IMPORTANT: 返回原始文本，不做归一化。信任高德 NLU 能力。

    Args:
        query: User query
        extracted_city: Already extracted city (to avoid re-extraction conflicts)

    Key insight: Use POSITIVE pattern matching, not residual extraction.

    Examples:
    - "北京市的鸟巢周边" -> "国家体育场" (from LANDMARK_ALIASES, high-frequency alias)
    - "上海静安寺附近的咖啡厅" -> "静安寺" (landmark suffix)
    - "成都春熙路附近的烧烤店" -> "春熙路" (POI suffix)
    - "南京新街口周边的日料" -> "新街口" (near pattern)
    - "福州国贸周边的加油站" -> "国贸" (原始文本，不归一化为"国贸中心")
    """
    # First, check for known landmarks (ONLY high-frequency aliases)
    for alias, official_name in LANDMARK_ALIASES.items():
        if alias in query:
            return official_name

    # Normalize query: remove spaces and punctuation
    q = re.sub(r'[\s，,。.!?？；;、]+', '', query)

    # Remove city from query before pattern matching (use provided city, don't re-extract)
    q_clean = q
    if extracted_city:
        city_base = extracted_city.replace("市", "")
        q_clean = q_clean.replace(extracted_city, "").replace(city_base, "")

    # Priority 2: Check 2-4 char landmarks with special suffixes
    # This prevents "静安寺" from being extracted as "静安区"
    # Note: "场" removed to avoid matching "停车场", "广场" is covered in Priority 4
    landmark_suffix_pattern = r'([\u4e00-\u9fa5]{2,4})(寺|庙|口|谷|碑|单|里|屯|井)'
    match = re.search(landmark_suffix_pattern, q_clean)
    if match:
        landmark = match.group(1) + match.group(2)
        # Skip "哪里" (functional word, not a landmark)
        if landmark.endswith("哪里"):
            pass  # Continue to Priority 3
        # Validate: not just "广场" alone (which is a category)
        # Also filter out false positives like "快递单" (should be "西单" only)
        elif len(landmark) >= 3:  # At least 3 chars like "静安寺", "新街口"
            # Additional validation for "单": must be a known landmark or followed by proximity words
            if landmark.endswith("单"):
                # Only accept if it's a known landmark like "西单"
                if landmark not in ["西单", "东单"]:
                    # Check if followed by proximity words (附近|周边|旁边)
                    if not re.search(rf'{re.escape(landmark)}(附近|周边|旁边|周围|一带)', q_clean):
                        return ""  # Skip false positives like "快递单"
            return landmark

    # Priority 3: Primary pattern: XX(附近|周边|旁边|周围|一带|哪里)
    # This captures the location anchor before the proximity indicator
    # Added "哪里" to handle "我在X，哪里有Y" pattern
    # Pre-clean functional prefixes from q_clean before pattern matching
    q_for_near = re.sub(r'^(我在|在|我去|去|我到|到|帮我找|找|帮我|给我)', '', q_clean)
    near_pattern = r'([\u4e00-\u9fa5A-Za-z0-9]{2,20})(附近|周边|旁边|周围|一带|哪里)'
    match = re.search(near_pattern, q_for_near)
    if match:
        region = match.group(1)
        region = _clean_anchor_region(region)
        if region and len(region) >= 2:
            return region  # 直接返回原始文本，不归一化

    # Priority 4: Fallback: POI suffix pattern (路|街|广场|公园|景区|大厦|中心|站 etc.)
    # Use non-greedy match and stop at "的" to avoid matching "五一广场的茶馆"
    poi_suffix_pattern = (
        r'([\u4e00-\u9fa5A-Za-z0-9]{2,20}?'  # Non-greedy match, max 20 chars
        r'(?:路|街道|街|巷|弄|号|大道|大街|胡同|里|段|村|镇|乡|'
        r'广场|公园|景区|风景区|景点|'
        r'大厦|中心|大楼|写字楼|'
        r'大学|学院|中学|小学|医院|'
        r'机场|火车站|高铁站|车站|地铁站|站|码头|'
        r'桥|塔|馆|'
        r'小区|苑|城|商圈|步行街|购物中心|商业街))'
        r'(?=的|$|，|,)'  # Lookahead: followed by "的" or end or comma
    )
    match = re.search(poi_suffix_pattern, q_clean)
    if match:
        region = match.group(1)
        region = _clean_anchor_region(region)
        # Validate: not a category keyword
        from .amap_type_codes import USER_CATEGORY_TO_AMAP_TYPE
        if region and len(region) >= 2 and region not in USER_CATEGORY_TO_AMAP_TYPE:
            return region  # 直接返回原始文本，不归一化

    # Return empty string - let caller fallback to district
    return ""


def _clean_anchor_region(region: str) -> str:
    """Clean extracted anchor region by removing functional prefixes and suffixes.
    
    Based on workflow node 1560882's _clean_region function.
    """
    if not region:
        return ""
    
    # Remove functional prefixes (请|麻烦|帮我找|找|推荐|查一下|我要|想|在|去|到)
    # Use word boundary to match single-char prefixes like "在"
    region = re.sub(
        r'^(?:'
        r'请|麻烦|帮忙|帮我找|帮我|给我|帮我一下|给我一下|'
        r'推荐|推荐一下|求推荐|'
        r'建议|建议一下|'
        r'查一下|搜一下|找一下|找|搜索|查找|查询|'
        r'我要|我想|想要|需要|想|'
        r'在|去|到|从|来'
        r')',
        '',
        region
    )
    
    # Remove trailing location indicators and "哪里"
    region = re.sub(r'(哪里|这里|那边|附近|周边|旁边|周围|一带)$', '', region)
    
    # Remove "的" at the end
    region = region.rstrip("的")
    
    return region.strip()


def _extract_sort_intent(query: str) -> tuple[str, str]:
    """Extract sort intent using regex pattern matching.
    
    Returns: (sort_by, sort_order)
    Examples:
    - "最近" -> ("distance", "asc")
    - "最好评" -> ("rating", "desc")
    """
    for keyword, (sort_by, order) in SORT_KEYWORDS.items():
        if keyword in query:
            return sort_by, order
    return "distance", "asc"


def _extract_constraints(query: str) -> dict[str, Any]:
    """Extract constraints using regex pattern matching.
    
    Examples: 24小时, 停车, wifi
    """
    constraints: dict[str, Any] = {}
    
    constraint_patterns = {
        "open_24h": r"(24小时|全天)",
        "has_parking": r"(停车|车位)",
        "has_wifi": r"(wifi|WIFI|无线)",
    }
    
    for key, pattern in constraint_patterns.items():
        if re.search(pattern, query, re.IGNORECASE):
            constraints[key] = True
    
    return constraints


def _calculate_confidence(intent: LocationIntent) -> float:
    """Calculate confidence score based on intent completeness.
    
    Scoring:
    - City: +1.0
    - Anchor POI: +1.5
    - Brand or category: +1.0 (REQUIRED - without this, confidence is capped at 0.25)
    - Constraints: +1.0
    Max: 4.5
    
    Key insight: A valid location query MUST have either brand or category.
    Without it, the query is likely not a POI search (e.g., "查询快递单", "密室逃脱").
    
    CRITICAL ASSUMPTION (for negative case detection):
    -----------------------------------------------
    This confidence cap (0.25 when no brand/category) relies on the assumption that
    unsupported POI types (密室逃脱, 剧本杀, VR体验馆, etc.) are NOT in the category
    dictionary (USER_CATEGORY_TO_AMAP_TYPE in amap_type_codes.py).
    
    If you add new POI types to the dictionary:
    1. Verify they are supported by Amap POI API (check official type codes)
    2. Test with negative cases to ensure no false positives
    3. If adding experimental/unsupported types, consider adding a separate
       "experimental_categories" set and exclude them from confidence calculation
    
    Failure mode if assumption breaks:
    - Adding "密室逃脱" to category dict → confidence jumps to 0.55+ → false positive
    - This failure is SILENT - no error, just wrong classification
    
    Mitigation:
    - Run test_negative_cases() after any dictionary updates
    - Consider adding explicit "unsupported_categories" blacklist in future
    """
    score = 0.0
    max_score = 4.5
    
    if intent.city:
        score += 1.0
    
    if intent.anchor_poi:
        score += 1.5
    
    if intent.brand or intent.category:
        score += 1.0
    
    if intent.constraints:
        score += 1.0
    
    # Without brand/category, cap confidence at 0.25
    # This ensures negative cases like "密室逃脱" get low confidence (< 0.3 threshold)
    confidence = score / max_score
    if not (intent.brand or intent.category):
        confidence = min(confidence, 0.25)
    
    return confidence
