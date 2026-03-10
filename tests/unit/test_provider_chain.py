"""Tests for provider chain management."""

import pytest

from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ToolProvider
from infra.tool_clients.provider_chain import ProviderChainManager


class MockSuccessProvider(ToolProvider):
    """Mock provider that always succeeds."""
    
    def execute(self, **kwargs) -> ProviderResult:
        return ProviderResult(
            ok=True,
            data={"message": "success"},
            provider_name=self.config.name,
        )
    
    def health_check(self) -> bool:
        return True


class MockFailProvider(ToolProvider):
    """Mock provider that always fails."""
    
    def execute(self, **kwargs) -> ProviderResult:
        return ProviderResult(
            ok=False,
            data=None,
            provider_name=self.config.name,
            error="mock_error",
        )
    
    def health_check(self) -> bool:
        return True


class MockTimeoutProvider(ToolProvider):
    """Mock provider that times out."""
    
    def execute(self, **kwargs) -> ProviderResult:
        raise TimeoutError("mock timeout")
    
    def health_check(self) -> bool:
        return True


def test_provider_chain_success():
    """Test successful execution with first provider."""
    manager = ProviderChainManager()
    manager.register_provider("success", MockSuccessProvider)
    
    config = [
        ProviderConfig(name="success", priority=1, timeout=1.0),
    ]
    manager.configure_chain("test_tool", config)
    
    result = manager.execute("test_tool")
    
    assert result.ok
    assert result.provider_name == "success"
    assert result.data == {"message": "success"}
    assert result.fallback_chain is None


def test_provider_chain_fallback():
    """Test fallback to second provider when first fails."""
    manager = ProviderChainManager()
    manager.register_provider("fail", MockFailProvider)
    manager.register_provider("success", MockSuccessProvider)
    
    config = [
        ProviderConfig(
            name="fail",
            priority=1,
            timeout=1.0,
            fallback_on_error=True,
        ),
        ProviderConfig(name="success", priority=2, timeout=1.0),
    ]
    manager.configure_chain("test_tool", config)
    
    result = manager.execute("test_tool")
    
    assert result.ok
    assert result.provider_name == "success"
    assert result.fallback_chain == ["fail:mock_error"]


def test_provider_chain_timeout_fallback():
    """Test fallback on timeout."""
    manager = ProviderChainManager()
    manager.register_provider("timeout", MockTimeoutProvider)
    manager.register_provider("success", MockSuccessProvider)
    
    config = [
        ProviderConfig(
            name="timeout",
            priority=1,
            timeout=1.0,
            fallback_on_timeout=True,
        ),
        ProviderConfig(name="success", priority=2, timeout=1.0),
    ]
    manager.configure_chain("test_tool", config)
    
    result = manager.execute("test_tool")
    
    assert result.ok
    assert result.provider_name == "success"
    assert result.fallback_chain == ["timeout:timeout"]


def test_provider_chain_all_fail():
    """Test when all providers fail."""
    manager = ProviderChainManager()
    manager.register_provider("fail1", MockFailProvider)
    manager.register_provider("fail2", MockFailProvider)
    
    config = [
        ProviderConfig(
            name="fail1",
            priority=1,
            timeout=1.0,
            fallback_on_error=True,
        ),
        ProviderConfig(
            name="fail2",
            priority=2,
            timeout=1.0,
            fallback_on_error=True,
        ),
    ]
    manager.configure_chain("test_tool", config)
    
    result = manager.execute("test_tool")
    
    assert not result.ok
    assert result.provider_name == "none"
    assert "All providers failed" in result.error
    assert result.fallback_chain == ["fail1:mock_error", "fail2:mock_error"]


def test_provider_chain_no_fallback_on_error():
    """Test that error doesn't trigger fallback when disabled."""
    manager = ProviderChainManager()
    manager.register_provider("fail", MockFailProvider)
    manager.register_provider("success", MockSuccessProvider)
    
    config = [
        ProviderConfig(
            name="fail",
            priority=1,
            timeout=1.0,
            fallback_on_error=False,  # Don't fallback
        ),
        ProviderConfig(name="success", priority=2, timeout=1.0),
    ]
    manager.configure_chain("test_tool", config)
    
    result = manager.execute("test_tool")
    
    assert not result.ok
    assert result.provider_name == "fail"
    assert result.fallback_chain is None


def test_provider_metrics():
    """Test provider metrics tracking."""
    manager = ProviderChainManager()
    manager.register_provider("success", MockSuccessProvider)
    
    config = [
        ProviderConfig(name="success", priority=1, timeout=1.0),
    ]
    manager.configure_chain("test_tool", config)
    
    # Execute multiple times
    for _ in range(5):
        manager.execute("test_tool")
    
    metrics = manager.get_metrics("test_tool", "success")
    
    assert "success" in metrics
    assert metrics["success"].total_calls == 5
    assert metrics["success"].success_calls == 5
    assert metrics["success"].failed_calls == 0
    assert metrics["success"].success_rate == 1.0


def test_update_provider_config():
    """Test runtime config updates."""
    manager = ProviderChainManager()
    manager.register_provider("success", MockSuccessProvider)
    
    config = [
        ProviderConfig(name="success", priority=1, timeout=1.0, enabled=True),
    ]
    manager.configure_chain("test_tool", config)
    
    # Disable provider
    manager.update_provider_config("test_tool", "success", enabled=False)
    
    result = manager.execute("test_tool")
    
    assert not result.ok
    assert "All providers failed" in result.error


def test_provider_priority_sorting():
    """Test that providers are sorted by priority."""
    manager = ProviderChainManager()
    manager.register_provider("low", MockSuccessProvider)
    manager.register_provider("high", MockSuccessProvider)
    
    # Register in wrong order
    config = [
        ProviderConfig(name="low", priority=10, timeout=1.0),
        ProviderConfig(name="high", priority=1, timeout=1.0),
    ]
    manager.configure_chain("test_tool", config)
    
    result = manager.execute("test_tool")
    
    # Should use high priority provider first
    assert result.provider_name == "high"
