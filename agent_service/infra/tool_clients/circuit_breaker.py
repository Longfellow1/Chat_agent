"""Circuit breaker for provider protection."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, skip provider
    HALF_OPEN = "half_open"  # Testing if provider recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Open circuit after N consecutive failures
    success_threshold: int = 2  # Close circuit after N consecutive successes in half-open
    timeout: float = 60.0  # Seconds to wait before trying half-open
    
    # Failure conditions
    count_timeout_as_failure: bool = True
    count_error_as_failure: bool = True


class CircuitBreaker:
    """Circuit breaker to protect against cascading failures."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.config.timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
        
        return self._state
    
    def is_open(self) -> bool:
        """Check if circuit is open (should skip provider)."""
        return self.state == CircuitState.OPEN
    
    def record_success(self) -> None:
        """Record successful execution."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                # Close circuit
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0
    
    def record_failure(self, is_timeout: bool = False) -> None:
        """Record failed execution."""
        # Check if this failure type should be counted
        should_count = (
            (is_timeout and self.config.count_timeout_as_failure) or
            (not is_timeout and self.config.count_error_as_failure)
        )
        
        if not should_count:
            return
        
        if self._state == CircuitState.HALF_OPEN:
            # Failure in half-open, reopen circuit
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()
            self._failure_count = 0
            self._success_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.config.failure_threshold:
                # Open circuit
                self._state = CircuitState.OPEN
                self._last_failure_time = time.time()
    
    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "time_until_half_open": max(0, self.config.timeout - (time.time() - self._last_failure_time))
            if self._state == CircuitState.OPEN else 0,
        }
