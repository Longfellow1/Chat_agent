"""LLM管理器 - 生产级功能：重试、熔断、监控、负载均衡"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from agent_service.infra.llm_clients.base import LLMClient
from agent_service.infra.llm_clients.llm_config import LLMServiceConfig
from agent_service.infra.llm_clients.llm_client_factory import LLMClientFactory

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常
    OPEN = "open"  # 熔断
    HALF_OPEN = "half_open"  # 半开（尝试恢复）


class LLMMetrics:
    """LLM指标收集"""
    
    def __init__(self) -> None:
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_latency_ms = 0.0
        self.circuit_breaker_trips = 0
        self.retries_triggered = 0
    
    def record_success(self, latency_ms: float) -> None:
        """记录成功请求"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_ms += latency_ms
    
    def record_failure(self) -> None:
        """记录失败请求"""
        self.total_requests += 1
        self.failed_requests += 1
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def get_avg_latency_ms(self) -> float:
        """获取平均延迟"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_ms / self.successful_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.get_success_rate(),
            "avg_latency_ms": self.get_avg_latency_ms(),
            "circuit_breaker_trips": self.circuit_breaker_trips,
            "retries_triggered": self.retries_triggered,
        }


class CircuitBreaker:
    """熔断器 - 防止级联故障"""
    
    def __init__(self, config: LLMServiceConfig) -> None:
        self.config = config.circuit_breaker_config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
    
    def call(self, func, *args, **kwargs) -> Any:
        """执行函数，应用熔断器逻辑"""
        if not self.config.enabled:
            return func(*args, **kwargs)
        
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.config.timeout_sec:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise RuntimeError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """成功时的处理"""
        self.failure_count = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                logger.info("Circuit breaker CLOSED")
    
    def _on_failure(self) -> None:
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


class RetryManager:
    """重试管理器"""
    
    def __init__(self, config: LLMServiceConfig) -> None:
        self.config = config.retry_config
    
    def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """执行函数，支持重试"""
        last_exception = None
        delay = self.config.initial_delay_sec
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # 检查是否应该重试
                if not self._should_retry(e, attempt):
                    raise
                
                if attempt < self.config.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.config.backoff_multiplier, self.config.max_delay_sec)
        
        raise last_exception
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.max_retries:
            return False
        
        error_msg = str(exception).lower()
        
        # 超时错误
        if "timeout" in error_msg and self.config.retry_on_timeout:
            return True
        
        # 速率限制
        if "rate limit" in error_msg and self.config.retry_on_rate_limit:
            return True
        
        # 临时错误
        if any(x in error_msg for x in ["temporarily", "unavailable", "connection"]):
            return True
        
        return False


class LLMManager:
    """LLM管理器 - 生产级功能"""
    
    def __init__(self, config: Optional[LLMServiceConfig] = None) -> None:
        self.config = config or LLMServiceConfig.from_env()
        self.client = LLMClientFactory.create_client(self.config)
        self.circuit_breaker = CircuitBreaker(self.config)
        self.retry_manager = RetryManager(self.config)
        self.metrics = LLMMetrics()
    
    def generate(self, user_query: str, system_prompt: str) -> str:
        """生成文本响应，包含重试和熔断逻辑"""
        start_time = time.time()
        
        try:
            # 应用熔断器和重试
            result = self.circuit_breaker.call(
                self.retry_manager.execute_with_retry,
                self.client.generate,
                user_query,
                system_prompt,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record_success(latency_ms)
            
            if self.config.enable_logging:
                logger.info(
                    f"LLM generation successful: "
                    f"model={self.config.model_name}, "
                    f"latency={latency_ms:.0f}ms"
                )
            
            return result
        except Exception as e:
            self.metrics.record_failure()
            
            if self.config.enable_logging:
                logger.error(f"LLM generation failed: {e}")
            
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.to_dict()
    
    def get_circuit_breaker_state(self) -> str:
        """获取熔断器状态"""
        return self.circuit_breaker.state.value
    
    def reset_metrics(self) -> None:
        """重置指标"""
        self.metrics = LLMMetrics()
