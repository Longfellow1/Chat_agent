"""OpenAI兼容接口提供商 - 支持任何OpenAI兼容的推理框架"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict, Optional

from infra.llm_clients.base import LLMClient
from infra.llm_clients.llm_config import LLMServiceConfig

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMClient):
    """OpenAI兼容接口客户端
    
    支持任何实现OpenAI API规范的推理框架，包括：
    - OpenAI官方API
    - Azure OpenAI
    - LocalAI
    - Text Generation WebUI
    - 其他兼容实现
    
    生产环境推荐配置：
    - 使用API密钥认证
    - 配置请求超时和重试
    - 监控API配额和成本
    - 使用专用API端点
    """
    
    def __init__(self, config: LLMServiceConfig) -> None:
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.model_name = config.model_name
        self.timeout = config.timeout_sec
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.top_p = config.top_p
        
        if not self.model_name:
            raise ValueError("model_name is required for OpenAI compatible provider")
        
        logger.info(f"Initialized OpenAI compatible provider: {self.base_url}")
    
    def generate(self, user_query: str, system_prompt: str) -> str:
        """生成文本响应"""
        payload = self._build_payload(user_query, system_prompt)
        headers = self._build_headers()
        
        try:
            response = self._make_request(payload, headers)
            return self._extract_response(response)
        except Exception as e:
            logger.error(f"OpenAI compatible generation failed: {e}")
            raise
    
    def _build_payload(self, user_query: str, system_prompt: str) -> Dict[str, Any]:
        """构建请求负载"""
        return {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": False,
        }
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _make_request(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    def _extract_response(self, response: Dict[str, Any]) -> str:
        """提取响应内容"""
        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"OpenAI API error: {error}")
        
        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError("No choices in OpenAI response")
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        if not content:
            raise RuntimeError("Empty content in OpenAI response")
        
        return content.strip()
