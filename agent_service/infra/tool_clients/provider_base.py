"""Tool provider base classes and interfaces."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResultType(Enum):
    """Result type for different provider outputs."""
    RAW = "raw"  # Raw search results (Bing-like, needs processing)
    SUMMARIZED = "summarized"  # AI-processed text (direct use)


class ProviderStatus(Enum):
    """Provider health status."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class ProviderConfig:
    """Provider configuration."""
    name: str
    priority: int  # Lower number = higher priority
    timeout: float
    max_retries: int = 1
    enabled: bool = True
    health_check_interval: int = 60  # seconds
    
    # Fallback conditions
    fallback_on_timeout: bool = True
    fallback_on_error: bool = True
    fallback_error_codes: list[str] = field(default_factory=list)


class ResultType(Enum):
    """Result type for different provider outputs."""
    RAW = "raw"  # Raw search results (Bing-like, needs processing)
    SUMMARIZED = "summarized"  # AI-processed text (direct use)


@dataclass
class ProviderResult:
    """Provider execution result."""
    ok: bool
    data: Any
    provider_name: str
    latency_ms: float = 0.0
    error: str | None = None
    fallback_chain: list[str] | None = None
    result_type: ResultType = ResultType.RAW  # Default to raw for backward compatibility


@dataclass
class ProviderMetrics:
    """Provider monitoring metrics."""
    total_calls: int = 0
    success_calls: int = 0
    failed_calls: int = 0
    timeout_count: int = 0
    error_count: int = 0
    fallback_count: int = 0
    total_latency_ms: float = 0.0
    last_success_time: float = 0.0
    last_failure_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.success_calls / self.total_calls
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.success_calls == 0:
            return 0.0
        return self.total_latency_ms / self.success_calls


class ToolProvider(ABC):
    """Base class for tool providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._status = ProviderStatus.AVAILABLE
        self._last_health_check = 0.0
        self._metrics = ProviderMetrics()
    
    @abstractmethod
    def execute(self, **kwargs) -> ProviderResult:
        """Execute tool call.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            ProviderResult with execution result
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check provider health.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    def is_available(self) -> bool:
        """Check if provider is available.
        
        Returns:
            True if available, False otherwise
        """
        if not self.config.enabled:
            return False
        
        if self._status == ProviderStatus.UNAVAILABLE:
            return False
        
        # Periodic health check
        now = time.time()
        if now - self._last_health_check > self.config.health_check_interval:
            try:
                healthy = self.health_check()
                self._status = ProviderStatus.AVAILABLE if healthy else ProviderStatus.DEGRADED
                self._last_health_check = now
            except Exception:
                self._status = ProviderStatus.DEGRADED
                self._last_health_check = now
        
        return True
    
    def record_success(self, latency_ms: float) -> None:
        """Record successful execution."""
        self._metrics.total_calls += 1
        self._metrics.success_calls += 1
        self._metrics.total_latency_ms += latency_ms
        self._metrics.last_success_time = time.time()
    
    def record_failure(self, error_type: str) -> None:
        """Record failed execution."""
        self._metrics.total_calls += 1
        self._metrics.failed_calls += 1
        self._metrics.last_failure_time = time.time()
        
        if error_type == "timeout":
            self._metrics.timeout_count += 1
        else:
            self._metrics.error_count += 1
    
    def record_fallback(self) -> None:
        """Record fallback to next provider."""
        self._metrics.fallback_count += 1
    
    def get_metrics(self) -> ProviderMetrics:
        """Get provider metrics.
        
        Returns:
            ProviderMetrics object
        """
        return self._metrics
