"""POI capability definitions and routing logic."""

from __future__ import annotations

from enum import Enum


class RetrievalSource(str, Enum):
    """POI retrieval source."""
    
    AMAP_MCP = "amap_mcp"  # Structured POI from Amap
    WEB_SEARCH = "web_search"  # Unstructured search from web
    HYBRID = "hybrid"  # Both sources


# High-confidence structured POI categories supported by Amap
STRUCTURED_POI_CATEGORIES = {
    # 餐饮 - 高频、标准化
    "餐厅", "饭店", "火锅", "烤肉", "烧烤", "快餐",
    "咖啡厅", "茶馆", "面馆",
    
    # 购物 - 标准化
    "便利店", "超市", "商场", "商店",
    
    # 服务 - 标准化
    "医院", "诊所", "药店",
    "酒店", "宾馆",
    "停车场", "加油站", "充电站",
    
    # 娱乐 - 主流
    "电影院", "KTV", "酒吧",
}

# Low-confidence or emerging POI categories (better handled by web search)
UNSTRUCTURED_POI_CATEGORIES = {
    # 新兴娱乐
    "密室", "密室逃脱", "剧本杀", "桌游", "桌游吧",
    
    # 小众/长尾
    "网红店", "打卡地", "特色体验", "手工坊",
    "livehouse", "脱口秀", "相声馆",
    
    # 细分餐饮（高德可能覆盖不全）
    "米其林", "黑珍珠", "必吃榜",
}

# Ambiguous categories that may need both sources
AMBIGUOUS_POI_CATEGORIES = {
    "西餐厅", "中餐厅", "日本料理", "韩国料理",  # 可能需要更精确的搜索
}


def get_retrieval_source(category: str) -> RetrievalSource:
    """Determine optimal retrieval source for a POI category.
    
    Args:
        category: POI category (e.g., "咖啡厅", "密室逃脱")
        
    Returns:
        RetrievalSource indicating which source(s) to use
    """
    if not category:
        return RetrievalSource.AMAP_MCP  # Default to structured search
    
    if category in STRUCTURED_POI_CATEGORIES:
        return RetrievalSource.AMAP_MCP
    
    if category in UNSTRUCTURED_POI_CATEGORIES:
        return RetrievalSource.WEB_SEARCH
    
    if category in AMBIGUOUS_POI_CATEGORIES:
        return RetrievalSource.HYBRID
    
    # Unknown category: try Amap first, fallback to web if no results
    return RetrievalSource.AMAP_MCP


def is_structured_category(category: str) -> bool:
    """Check if category is well-supported by structured POI data."""
    return category in STRUCTURED_POI_CATEGORIES


def is_unstructured_category(category: str) -> bool:
    """Check if category requires unstructured web search."""
    return category in UNSTRUCTURED_POI_CATEGORIES
