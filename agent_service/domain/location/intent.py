"""Location intent data model."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class AnchorType(str, Enum):
    """Anchor POI type."""

    LANDMARK = "landmark"  # 地标（鸟巢、世博源）
    ADDRESS = "address"  # 地址（xx街道xx号）
    POI = "poi"  # POI（餐厅、医院）


class SortBy(str, Enum):
    """Sort strategy."""

    DISTANCE = "distance"
    RATING = "rating"
    PRICE = "price"


@dataclass
class LocationIntent:
    """Structured location intent for find_nearby / plan_trip."""

    # Geographic hierarchy
    city: str = ""
    district: str = ""
    street: str = ""

    # Anchor POI information
    anchor_poi: str = ""
    anchor_type: AnchorType = AnchorType.LANDMARK

    # Target information
    brand: str = ""
    category: str = ""
    keywords: list[str] = field(default_factory=list)

    # Constraints
    sort_by: SortBy = SortBy.DISTANCE
    sort_order: str = "asc"  # asc | desc
    constraints: dict[str, Any] = field(default_factory=dict)

    # Metadata
    raw_query: str = ""
    confidence: float = 1.0
    extraction_source: str = "rule"  # rule | llm | hybrid

    def is_complete(self) -> bool:
        """Check if intent is complete for tool execution."""
        # For find_nearby: need city and (anchor_poi or category)
        return bool(self.city and (self.anchor_poi or self.category))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to strings
        data["anchor_type"] = self.anchor_type.value
        data["sort_by"] = self.sort_by.value
        return data

    def to_tool_args(self) -> dict[str, Any]:
        """Convert to tool arguments for MCP gateway.
        
        简化策略（信任高德 NLU）:
        - 如果有 anchor_poi: 拼接 "location + keyword" 作为 keyword
        - 如果没有 anchor_poi: 只用 category/brand 作为 keyword
        - 始终传递 city
        - 模糊词映射: "好吃的" -> "餐厅", "好玩的" -> "景点" 等
        
        示例:
        - "福州国贸周边的加油站" → city="福州", keyword="国贸 加油站"
        - "上海的咖啡厅" → city="上海", keyword="咖啡厅"
        - "北京国贸附近有什么好吃的" → city="北京", keyword="国贸 餐厅"
        """
        import re
        from .dictionaries import normalize_fuzzy_category
        
        args: dict[str, Any] = {}

        # 构建 keyword
        keyword_parts = []
        
        # 如果有 anchor_poi，清理前缀后加入到 keyword
        if self.anchor_poi:
            # 清理可能残留的前缀（"我在"、"我找"等）
            cleaned_anchor = re.sub(r'^(我在|在|我去|去|我到|到|我找|找|帮我找|帮我|给我)', '', self.anchor_poi)
            if cleaned_anchor:
                keyword_parts.append(cleaned_anchor)
        
        # 加入 brand 或 category（先做模糊词映射）
        if self.brand:
            keyword_parts.append(self.brand)
        elif self.category:
            # 模糊词映射: "好吃的" -> "餐厅", "好玩的" -> "景点"
            normalized_category = normalize_fuzzy_category(self.category)
            keyword_parts.append(normalized_category)
        
        # 拼接 keyword
        if keyword_parts:
            args["keyword"] = " ".join(keyword_parts)

        # 始终包含 city
        if self.city:
            args["city"] = self.city

        return args
