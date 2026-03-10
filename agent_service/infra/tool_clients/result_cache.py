"""Simple result cache for auto show demo."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CacheEntry:
    """Cache entry."""
    key: str
    value: Any
    timestamp: float
    ttl: float  # Time to live in seconds
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return time.time() - self.timestamp > self.ttl


class ResultCache:
    """Simple in-memory cache for tool results."""
    
    def __init__(self, default_ttl: float = 3600):
        """Initialize cache.
        
        Args:
            default_ttl: Default time to live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, tool_name: str, **kwargs) -> str:
        """Make cache key from tool name and arguments.
        
        Args:
            tool_name: Tool name
            **kwargs: Tool arguments
            
        Returns:
            Cache key (hash)
        """
        # Sort kwargs for consistent hashing
        sorted_args = sorted(kwargs.items())
        key_str = f"{tool_name}:{sorted_args}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, tool_name: str, **kwargs) -> Any | None:
        """Get cached result.
        
        Args:
            tool_name: Tool name
            **kwargs: Tool arguments
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(tool_name, **kwargs)
        
        if key in self._cache:
            entry = self._cache[key]
            
            if entry.is_expired:
                # Remove expired entry
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.value
        
        self._misses += 1
        return None
    
    def set(self, tool_name: str, value: Any, ttl: float | None = None, **kwargs) -> None:
        """Set cache entry.
        
        Args:
            tool_name: Tool name
            value: Result to cache
            ttl: Time to live in seconds (None = use default)
            **kwargs: Tool arguments
        """
        key = self._make_key(tool_name, **kwargs)
        
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl if ttl is not None else self._default_ttl,
        )
        
        self._cache[key] = entry
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }
    
    def get_status_report(self) -> str:
        """Get formatted status report."""
        stats = self.get_stats()
        
        return (
            f"=== Cache Status ===\n"
            f"Size: {stats['size']} entries\n"
            f"Hits: {stats['hits']}\n"
            f"Misses: {stats['misses']}\n"
            f"Hit Rate: {stats['hit_rate']:.1%}\n"
            f"Total Requests: {stats['total_requests']}"
        )
