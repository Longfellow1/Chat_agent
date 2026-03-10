"""Unit tests for BaiduAISearchProvider."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add agent_service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from infra.tool_clients.provider_base import ProviderConfig, ResultType
from infra.tool_clients.providers.baidu_providers import BaiduAISearchProvider


@pytest.fixture
def provider_config():
    """Create provider config for testing."""
    return ProviderConfig(
        name="baidu_ai_search",
        priority=2,
        timeout=10.0,
        enabled=True,
    )


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    with patch("openai.OpenAI") as mock:
        yield mock


class TestBaiduAISearchProvider:
    """Test BaiduAISearchProvider."""
    
    def test_init_with_api_key(self, provider_config, mock_openai_client):
        """Test provider initialization with API key."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        provider = BaiduAISearchProvider(provider_config)
        
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://qianfan.baidubce.com/v2/ai_search"
        assert provider.model == "ernie-3.5-8k"
        assert provider.timeout == 10.0
        mock_openai_client.assert_called_once()
    
    def test_init_without_api_key(self, provider_config):
        """Test provider initialization without API key."""
        os.environ.pop("BAIDU_QIANFAN_API_KEY", None)
        
        provider = BaiduAISearchProvider(provider_config)
        
        assert provider.api_key == ""
        assert provider.client is None
    
    def test_health_check_with_client(self, provider_config, mock_openai_client):
        """Test health check with valid client."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        provider = BaiduAISearchProvider(provider_config)
        
        assert provider.health_check() is True
    
    def test_health_check_without_client(self, provider_config):
        """Test health check without client."""
        os.environ.pop("BAIDU_QIANFAN_API_KEY", None)
        
        provider = BaiduAISearchProvider(provider_config)
        
        assert provider.health_check() is False
    
    def test_execute_without_client(self, provider_config):
        """Test execute without client."""
        os.environ.pop("BAIDU_QIANFAN_API_KEY", None)
        
        provider = BaiduAISearchProvider(provider_config)
        result = provider.execute(query="test query")
        
        assert result.ok is False
        assert result.error == "baidu_api_key_missing_or_openai_not_installed"
        assert result.result_type == ResultType.SUMMARIZED
    
    def test_execute_without_query(self, provider_config, mock_openai_client):
        """Test execute without query."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        provider = BaiduAISearchProvider(provider_config)
        result = provider.execute()
        
        assert result.ok is False
        assert result.error == "missing_query"
        assert result.result_type == ResultType.SUMMARIZED
    
    def test_execute_success(self, provider_config, mock_openai_client):
        """Test successful execution."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        # Mock response
        mock_response = MagicMock()
        mock_response.code = None
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI搜索结果：今天的财经新闻..."
        mock_response.model_dump.return_value = {"id": "test"}
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client
        
        provider = BaiduAISearchProvider(provider_config)
        result = provider.execute(query="今天有哪些财经新闻")
        
        assert result.ok is True
        assert result.result_type == ResultType.SUMMARIZED
        assert result.data.text == "AI搜索结果：今天的财经新闻..."
        assert result.data.raw["provider"] == "baidu_ai_search"
        assert result.data.raw["query"] == "今天有哪些财经新闻"
    
    def test_execute_rate_limit_error(self, provider_config, mock_openai_client):
        """Test rate limit error handling."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.code = "rpm_rate_limit_exceeded"
        mock_response.message = "Rate limit reached for RPM"
        mock_response.choices = None
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client
        
        provider = BaiduAISearchProvider(provider_config)
        result = provider.execute(query="test query")
        
        assert result.ok is False
        assert "rate_limit" in result.error
        assert result.result_type == ResultType.SUMMARIZED
    
    def test_execute_empty_response(self, provider_config, mock_openai_client):
        """Test empty response handling."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.code = None
        mock_response.choices = []
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client
        
        provider = BaiduAISearchProvider(provider_config)
        result = provider.execute(query="test query")
        
        assert result.ok is False
        assert result.error == "empty_response"
        assert result.result_type == ResultType.SUMMARIZED
    
    def test_execute_exception(self, provider_config, mock_openai_client):
        """Test exception handling."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        # Mock exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Network error")
        mock_openai_client.return_value = mock_client
        
        provider = BaiduAISearchProvider(provider_config)
        result = provider.execute(query="test query")
        
        assert result.ok is False
        assert "baidu_error" in result.error
        assert "Network error" in result.error
        assert result.result_type == ResultType.SUMMARIZED
    
    def test_execute_timeout_exception(self, provider_config, mock_openai_client):
        """Test timeout exception handling."""
        os.environ["BAIDU_QIANFAN_API_KEY"] = "test-key"
        
        # Mock timeout exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("timeout exceeded")
        mock_openai_client.return_value = mock_client
        
        provider = BaiduAISearchProvider(provider_config)
        result = provider.execute(query="test query")
        
        assert result.ok is False
        assert "timeout" in result.error
        assert result.result_type == ResultType.SUMMARIZED
