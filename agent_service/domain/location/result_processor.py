"""Result processor for location search results - Rerank and filter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .intent import LocationIntent, SortBy


class ResultProcessor(ABC):
    """Base class for result processors."""
    
    priority: int = 100  # Lower number = higher priority
    
    @abstractmethod
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Process results based on intent.
        
        Args:
            results: List of POI results from API
            intent: Parsed location intent
            
        Returns:
            Processed results
        """
        pass
    
    def __lt__(self, other: ResultProcessor) -> bool:
        """Compare processors by priority for sorting."""
        return self.priority < other.priority


class BrandFilter(ResultProcessor):
    """Filter results by brand name."""
    
    priority = 10
    
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Filter results to match brand."""
        if not intent.brand:
            return results
        
        filtered = []
        for result in results:
            name = result.get("name", "")
            # Check if brand appears in POI name (case-insensitive, flexible matching)
            # Support variations: 711, 7-11, 7-Eleven
            brand_lower = intent.brand.lower().replace("-", "").replace(" ", "")
            name_lower = name.lower().replace("-", "").replace(" ", "")
            
            if brand_lower in name_lower:
                filtered.append(result)
        
        return filtered


# CategoryFilter 已删除
# 原因: 简化方案后高德返回的 POI 没有 type 字段，无法基于 type 过滤
# 当前策略: 信任高德 NLU（相关性测试显示 90%，样本量待扩大）
# 如需启用: 参考 spec/m1_critical_issues_analysis.md 选项B（基于 POI name 过滤）
# 
# 历史代码（已删除）:
# class CategoryFilter(ResultProcessor):
#     priority = 15
#     def process(self, results, intent):
#         # 过滤逻辑基于 poi.get("type")，但简化方案后 type=None
#         ...


class DistanceSorter(ResultProcessor):
    """Sort results by distance."""
    
    priority = 50
    
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Sort results by distance."""
        if intent.sort_by != SortBy.DISTANCE:
            return results
        
        # Sort by distance (ascending or descending)
        reverse = intent.sort_order == "desc"
        
        def get_distance(result: dict[str, Any]) -> float:
            distance = result.get("distance")
            if distance is None:
                return 999999.0
            # Handle both string and numeric distance
            if isinstance(distance, str):
                try:
                    return float(distance)
                except ValueError:
                    return 999999.0
            return float(distance)
        
        return sorted(results, key=get_distance, reverse=reverse)


class RatingSorter(ResultProcessor):
    """Sort results by rating."""
    
    priority = 51
    
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Sort results by rating."""
        if intent.sort_by != SortBy.RATING:
            return results
        
        # Sort by rating (descending by default)
        reverse = intent.sort_order != "asc"
        
        def get_rating(result: dict[str, Any]) -> float:
            # Check multiple possible rating fields
            rating = result.get("rating") or result.get("score") or result.get("biz_ext", {}).get("rating")
            if rating is None:
                return 0.0
            if isinstance(rating, str):
                try:
                    return float(rating)
                except ValueError:
                    return 0.0
            return float(rating)
        
        return sorted(results, key=get_rating, reverse=reverse)


class PriceSorter(ResultProcessor):
    """Sort results by price."""
    
    priority = 52
    
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Sort results by price."""
        if intent.sort_by != SortBy.PRICE:
            return results
        
        # Sort by price (ascending by default)
        reverse = intent.sort_order == "desc"
        
        def get_price(result: dict[str, Any]) -> float:
            # Check multiple possible price fields
            price = result.get("price") or result.get("avg_price") or result.get("biz_ext", {}).get("cost")
            if price is None:
                return 999999.0
            if isinstance(price, str):
                try:
                    return float(price)
                except ValueError:
                    return 999999.0
            return float(price)
        
        return sorted(results, key=get_price, reverse=reverse)


class Open24hFilter(ResultProcessor):
    """Filter results that are open 24 hours."""
    
    priority = 20
    
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Filter results that are open 24 hours."""
        if not intent.constraints.get("open_24h"):
            return results
        
        filtered = []
        for result in results:
            # Check if POI is open 24 hours
            # This depends on API response structure
            business_hours = result.get("business_hours", "")
            if "24" in business_hours or "全天" in business_hours:
                filtered.append(result)
        
        return filtered if filtered else results  # Return all if no 24h found


class TopNSelector(ResultProcessor):
    """Select top N results."""
    
    priority = 90
    
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Select top N results."""
        # Default limit: 5 results
        limit = 5
        
        # Check if user specified a number
        # e.g., "最近的3家711" -> limit=3
        # This should be extracted in intent parsing
        if hasattr(intent, "limit") and intent.limit:
            limit = intent.limit
        
        return results[:limit]


class ResultProcessorChain:
    """Chain of result processors."""
    
    def __init__(self):
        self.processors: list[ResultProcessor] = []
    
    def register(self, processor: ResultProcessor) -> None:
        """Register a processor."""
        self.processors.append(processor)
        # Sort by priority (lower number = higher priority)
        self.processors.sort()
    
    def process(self, results: list[dict[str, Any]], intent: LocationIntent) -> list[dict[str, Any]]:
        """Process results through the chain."""
        processed = results
        
        for processor in self.processors:
            processed = processor.process(processed, intent)
            
            # Stop if no results left
            if not processed:
                break
        
        return processed


def create_default_processor_chain() -> ResultProcessorChain:
    """Create default processor chain for location results.
    
    注意: CategoryFilter 已删除
    - 原因: 简化方案后高德返回的 POI 没有 type 字段，CategoryFilter 无法工作
    - 当前策略: 信任高德 NLU（相关性测试显示 90%）
    - 如需启用: 参考 spec/m1_critical_issues_analysis.md 选项B（基于 name 过滤）
    """
    chain = ResultProcessorChain()
    
    # Register processors in priority order
    chain.register(BrandFilter())
    # CategoryFilter 已删除 - 见上方注释
    chain.register(Open24hFilter())
    chain.register(DistanceSorter())
    chain.register(RatingSorter())
    chain.register(PriceSorter())
    chain.register(TopNSelector())
    
    return chain
