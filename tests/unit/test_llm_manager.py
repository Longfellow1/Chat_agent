"""LLM管理器单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from agent_service.infra.llm_clients.llm_config import (
    LLMServiceConfig,
    LLMProvider,
    Environment,
    RetryConfig,
    CircuitBreakerConfig,
)
from agent_service.infra.llm_clients.llm_manager import (
    LLMManager,
    CircuitBreaker,
    RetryManager,
    LLMMetrics,
    CircuitBreakerState,
)


class TestLLMMetrics:
    """测试LLM指标收集"""
    
    def test_record_success(self):
        metrics = LLMMetrics()
        metrics.record_success(100.0)
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.total_latency_ms == 100.0
    
    def test_record_failure(self):
        metrics = LLMMetrics()
        metrics.record_failure()
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
    
    def test_success_rate(self):
        metrics = LLMMetrics()
        metrics.record_success(100.0)
        metrics.record_success(100.0)
        metrics.record_failure()
        
        assert metrics.get_success_rate() == pytest.approx(2/3)
    
    def test_avg_latency(self):
        metrics = LLMMetrics()
        metrics.record_success(100.0)
        metrics.record_success(200.0)
        
        assert metrics.get_avg_latency_ms() == pytest.approx(150.0)


class TestCircuitBreaker:
    """测试熔断器"""
    
    def test_circuit_breaker_closed_state(self):
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
        )
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_circuit_breaker_opens_after_failures(self):
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
            circuit_breaker_config=CircuitBreakerConfig(
                enabled=True,
                failure_threshold=3,
            ),
        )
        cb = CircuitBreaker(config)
        
        def failing_func():
            raise RuntimeError("Test error")
        
        # 失败3次后熔断器打开
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(failing_func)
        
        assert cb.state == CircuitBreakerState.OPEN
    
    def test_circuit_breaker_disabled(self):
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
            circuit_breaker_config=CircuitBreakerConfig(enabled=False),
        )
        cb = CircuitBreaker(config)
        
        def failing_func():
            raise RuntimeError("Test error")
        
        # 即使失败也不会打开熔断器
        with pytest.raises(RuntimeError):
            cb.call(failing_func)
        
        assert cb.state == CircuitBreakerState.CLOSED


class TestRetryManager:
    """测试重试管理器"""
    
    def test_retry_on_timeout(self):
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
            retry_config=RetryConfig(
                max_retries=2,
                initial_delay_sec=0.01,
                retry_on_timeout=True,
            ),
        )
        rm = RetryManager(config)
        
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Timeout")
            return "success"
        
        result = rm.execute_with_retry(failing_func)
        
        assert result == "success"
        assert call_count == 3
    
    def test_no_retry_on_permanent_error(self):
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
            retry_config=RetryConfig(max_retries=2),
        )
        rm = RetryManager(config)
        
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")
        
        with pytest.raises(ValueError):
            rm.execute_with_retry(failing_func)
        
        # 不应该重试
        assert call_count == 1


class TestLLMManager:
    """测试LLM管理器"""
    
    @patch('agent_service.infra.llm_clients.llm_client_factory.LLMClientFactory.create_client')
    def test_generate_success(self, mock_create_client):
        # 模拟客户端
        mock_client = Mock()
        mock_client.generate.return_value = "Test response"
        mock_create_client.return_value = mock_client
        
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
        )
        
        manager = LLMManager(config)
        response = manager.generate("Hello", "You are helpful")
        
        assert response == "Test response"
        assert manager.metrics.successful_requests == 1
    
    @patch('agent_service.infra.llm_clients.llm_client_factory.LLMClientFactory.create_client')
    def test_generate_with_retry(self, mock_create_client):
        # 模拟客户端，第一次超时，第二次成功
        mock_client = Mock()
        mock_client.generate.side_effect = [
            TimeoutError("Timeout"),
            "Test response",
        ]
        mock_create_client.return_value = mock_client
        
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
            retry_config=RetryConfig(
                max_retries=2,
                initial_delay_sec=0.01,
            ),
        )
        
        manager = LLMManager(config)
        response = manager.generate("Hello", "You are helpful")
        
        assert response == "Test response"
        assert mock_client.generate.call_count == 2
    
    @patch('agent_service.infra.llm_clients.llm_client_factory.LLMClientFactory.create_client')
    def test_get_metrics(self, mock_create_client):
        mock_client = Mock()
        mock_client.generate.return_value = "Test response"
        mock_create_client.return_value = mock_client
        
        config = LLMServiceConfig(
            provider=LLMProvider.VLLM,
            environment=Environment.DEV,
            base_url="http://localhost:8000",
            model_name="test-model",
        )
        
        manager = LLMManager(config)
        manager.generate("Hello", "You are helpful")
        
        metrics = manager.get_metrics()
        
        assert metrics["total_requests"] == 1
        assert metrics["successful_requests"] == 1
        assert metrics["success_rate"] == 1.0
