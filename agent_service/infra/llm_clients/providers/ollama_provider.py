"""Ollama推理框架提供商 - 轻量级本地推理"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict

from infra.llm_clients.base import LLMClient
from infra.llm_clients.llm_config import LLMServiceConfig

logger = logging.getLogger(__name__)


class OllamaProvider(LLMClient):
    """Ollama推理框架客户端
    
    Ollama是一个轻量级的本地LLM推理框架，特点：
    - 易于部署和使用
    - 支持多种开源模型
    - 低资源占用
    - 适合开发和小规模生产环境
    
    生产环境推荐配置：
    - 部署在应用服务器或专用推理节点
    - 配置模型预加载
    - 使用连接池优化性能
    """
    
    def __init__(self, config: LLMServiceConfig) -> None:
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.model_name = config.model_name
        self.timeout = config.timeout_sec
        self.temperature = config.temperature
        self.top_p = config.top_p
        
        logger.info(f"Initialized Ollama provider: {self.base_url}")
    
    def generate(self, user_query: str, system_prompt: str) -> str:
        """生成文本响应"""
        payload = self._build_payload(user_query, system_prompt)
        
        try:
            response = self._make_request(payload)
            return self._extract_response(response)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
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
            "top_p": self.top_p,
            "stream": False,
        }
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送HTTP请求"""
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    def _extract_response(self, response: Dict[str, Any]) -> str:
        """提取响应内容"""
        message = response.get("message", {})
        content = message.get("content", "")
        
        if not content:
            raise RuntimeError("Empty response from Ollama")
        
        return content.strip()
