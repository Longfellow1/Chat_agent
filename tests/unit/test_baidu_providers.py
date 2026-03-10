"""Unit tests for Baidu providers."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add agent_service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from infra.tool_clients.provider_base import ProviderConfig, ResultType
from infra.tool_clients.providers.baidu_baike_provider import BaiduBaikeProvider
from infra.tool_clients.providers.baidu_search_mcp_provider import BaiduSearchMCPProvider


class TestBaiduBaikeProvider:
    """Test Baidu Baike provider."""
    
    def test_missing_access_key(self):
        """Test error when access key is missing."""
        config = ProviderConfig(
            name="baidu_baike",
            priority=1,
            timeout=2.5,
        )
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": ""}, clear=False):
            provider = BaiduBaikeProvider(config)
            result = provider.execute(query="什么是电动汽车")
        
        assert not result.ok
        assert result.error == "baidu_access_key_missing"
        assert result.result_type == ResultType.SUMMARIZED
    
    def test_missing_query(self):
        """Test error when query is missing."""
        config = ProviderConfig(
            name="baidu_baike",
            priority=1,
            timeout=2.5,
        )
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduBaikeProvider(config)
            result = provider.execute()
        
        assert not result.ok
        assert result.error == "missing_query"
        assert result.result_type == ResultType.SUMMARIZED
    
    @patch("infra.tool_clients.providers.baidu_baike_provider.requests.post")
    def test_successful_query(self, mock_post):
        """Test successful encyclopedia query."""
        config = ProviderConfig(
            name="baidu_baike",
            priority=1,
            timeout=2.5,
        )
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "summary": "电动汽车是指以车载电源为动力...",
                "url": "https://baike.baidu.com/item/电动汽车",
            }
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduBaikeProvider(config)
            result = provider.execute(query="什么是电动汽车")
        
        assert result.ok
        assert result.result_type == ResultType.SUMMARIZED
        assert result.data.ok
        assert "电动汽车" in result.data.text
        assert result.data.raw["provider"] == "baidu_baike"
    
    @patch("infra.tool_clients.providers.baidu_baike_provider.requests.post")
    def test_no_content(self, mock_post):
        """Test error when no content returned."""
        config = ProviderConfig(
            name="baidu_baike",
            priority=1,
            timeout=2.5,
        )
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "summary": "",
            }
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduBaikeProvider(config)
            result = provider.execute(query="什么是电动汽车")
        
        assert not result.ok
        assert result.error == "no_content"
    
    def test_health_check(self):
        """Test health check."""
        config = ProviderConfig(
            name="baidu_baike",
            priority=1,
            timeout=2.5,
        )
        
        # With key
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduBaikeProvider(config)
            assert provider.health_check()
        
        # Without key
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": ""}, clear=False):
            provider = BaiduBaikeProvider(config)
            assert not provider.health_check()


class TestBaiduSearchMCPProvider:
    """Test Baidu Search MCP provider."""
    
    def test_missing_access_key(self):
        """Test error when access key is missing."""
        config = ProviderConfig(
            name="baidu_search_mcp",
            priority=1,
            timeout=3.0,
        )
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": ""}, clear=False):
            provider = BaiduSearchMCPProvider(config)
            result = provider.execute(query="特斯拉价格")
        
        assert not result.ok
        assert result.error == "baidu_access_key_missing"
        assert result.result_type == ResultType.RAW
    
    def test_missing_query(self):
        """Test error when query is missing."""
        config = ProviderConfig(
            name="baidu_search_mcp",
            priority=1,
            timeout=3.0,
        )
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduSearchMCPProvider(config)
            result = provider.execute()
        
        assert not result.ok
        assert result.error == "missing_query"
        assert result.result_type == ResultType.RAW
    
    @patch("infra.tool_clients.search_result_processor.process_search_results")
    @patch("infra.tool_clients.providers.baidu_search_mcp_provider.requests.post")
    def test_successful_search(self, mock_post, mock_process):
        """Test successful search query."""
        config = ProviderConfig(
            name="baidu_search_mcp",
            priority=1,
            timeout=3.0,
        )
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "search_results": [
                    {
                        "title": "特斯拉 Model 3 价格",
                        "url": "https://example.com/tesla",
                        "snippet": "特斯拉 Model 3 售价...",
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # Mock processor
        mock_process.return_value = [
            {
                "title": "特斯拉 Model 3 价格",
                "url": "https://example.com/tesla",
                "snippet": "特斯拉 Model 3 售价...",
                "credibility": 8,
            }
        ]
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduSearchMCPProvider(config)
            result = provider.execute(query="特斯拉价格")
        
        assert result.ok
        assert result.result_type == ResultType.RAW
        assert result.data.ok
        assert "特斯拉" in result.data.text
        assert result.data.raw["provider"] == "baidu_search_mcp"
    
    @patch("infra.tool_clients.providers.baidu_search_mcp_provider.requests.post")
    def test_no_results(self, mock_post):
        """Test error when no results returned."""
        config = ProviderConfig(
            name="baidu_search_mcp",
            priority=1,
            timeout=3.0,
        )
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "search_results": []
            }
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduSearchMCPProvider(config)
            result = provider.execute(query="特斯拉价格")
        
        assert not result.ok
        assert result.error == "no_results"
    
    def test_health_check(self):
        """Test health check."""
        config = ProviderConfig(
            name="baidu_search_mcp",
            priority=1,
            timeout=3.0,
        )
        
        # With key
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": "test-key"}, clear=False):
            provider = BaiduSearchMCPProvider(config)
            assert provider.health_check()
        
        # Without key
        with patch.dict(os.environ, {"BAIDU_BCE_ACCESS_KEY": ""}, clear=False):
            provider = BaiduSearchMCPProvider(config)
            assert not provider.health_check()
