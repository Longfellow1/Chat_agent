"""Response templates for location search results."""

from __future__ import annotations

import random
from typing import Any

from .intent import LocationIntent


# Template categories for different scenarios
SINGLE_RESULT_TEMPLATES = [
    "{name}在{address}",
    "找到了{name}，地址是{address}",
    "{name}，位于{address}",
    "这是{name}，地址：{address}",
]

MULTIPLE_RESULTS_TEMPLATES = [
    "找到{count}个{category}：",
    "为您找到{count}个{category}：",
    "附近有{count}个{category}：",
    "共找到{count}个{category}：",
]

DISTANCE_SORTED_TEMPLATES = [
    "按距离排序，最近的是{name}（{distance}米）",
    "离您最近的是{name}，距离{distance}米",
    "{name}距离最近，约{distance}米",
]

RATING_SORTED_TEMPLATES = [
    "按评分排序，{name}评分最高（{rating}分）",
    "评分最高的是{name}，{rating}分",
    "{name}口碑最好，评分{rating}",
]

NO_RESULTS_TEMPLATES = [
    "抱歉，没有找到符合条件的{category}",
    "附近暂时没有{category}",
    "未找到{category}，您可以换个地点试试",
]


def format_location_results(
    results: list[dict[str, Any]],
    intent: LocationIntent,
    original_count: int | None = None,
) -> str:
    """Format location search results using templates.
    
    Args:
        results: Processed POI results
        intent: Parsed location intent
        original_count: Original result count before filtering
        
    Returns:
        Formatted response text
    """
    # No results
    if not results:
        template = random.choice(NO_RESULTS_TEMPLATES)
        return template.format(
            category=intent.category or intent.brand or "结果"
        )
    
    # Single result
    if len(results) == 1:
        return _format_single_result(results[0], intent)
    
    # Multiple results
    return _format_multiple_results(results, intent, original_count)


def _format_single_result(result: dict[str, Any], intent: LocationIntent) -> str:
    """Format single result."""
    name = result.get("name", "未知")
    address = result.get("address", "")
    distance = result.get("distance", "")
    
    # If sorted by distance, emphasize distance
    if intent.sort_by.value == "distance" and distance:
        template = random.choice(DISTANCE_SORTED_TEMPLATES)
        return template.format(name=name, distance=distance)
    
    # Default: name + address
    if address:
        template = random.choice(SINGLE_RESULT_TEMPLATES)
        return template.format(name=name, address=address)
    
    return name


def _format_multiple_results(
    results: list[dict[str, Any]],
    intent: LocationIntent,
    original_count: int | None,
) -> str:
    """Format multiple results."""
    lines = []
    
    # Header
    category = intent.category or intent.brand or "结果"
    count = len(results)
    
    template = random.choice(MULTIPLE_RESULTS_TEMPLATES)
    header = template.format(count=count, category=category)
    lines.append(header)
    
    # List results (top 5)
    for i, result in enumerate(results[:5], 1):
        name = result.get("name", "未知")
        distance = result.get("distance", "")
        address = result.get("address", "")
        
        # Format: "1. Name (distance) - address"
        parts = [f"{i}. {name}"]
        
        if distance:
            parts.append(f"（{distance}米）")
        
        if address:
            parts.append(f" - {address}")
        
        lines.append("".join(parts))
    
    # Footer: show if filtered
    if original_count and original_count > count:
        lines.append(f"\n（已从{original_count}个结果中筛选）")
    
    return "\n".join(lines)


def can_use_template(results: list[dict[str, Any]]) -> bool:
    """Check if template can be used for results.
    
    Args:
        results: POI results
        
    Returns:
        True if template can fill required fields
    """
    if not results:
        return True  # Can use NO_RESULTS template
    
    # Check if first result has required fields
    first = results[0]
    
    # Minimum requirement: name field
    if "name" not in first:
        return False
    
    return True
