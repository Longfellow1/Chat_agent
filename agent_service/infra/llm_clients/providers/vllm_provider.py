"""vLLM推理框架提供商 - 高性能推理"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict

from agent_service.infra.llm_clients.base import LLMClient
from agent_service.infra.llm_clients.llm_config import LLMServiceConfig

logger = logging.getLogger(__name__)


class VLLMProvider(LLMClient):
    """vLLM推理框架客户端
    
    vLLM是一个高性能的LLM推理框架，支持：
    - 高吞吐量推理
    - 连续批处理
    - 分页注意力机制
    - 多GPU支持
    
    生产环境推荐配置：
    - 部署在专用GPU服务器
    - 使用负载均衡器分散请求
    - 配置熔断器和重试机制
    """
    
    def __init__(self, config: LLMServiceConfig) -> None:
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.model_name = config.model_name
        self.timeout = config.timeout_sec
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.top_p = config.top_p
        self.top_k = config.top_k
        
        logger.info(f"Initialized vLLM provider: {self.base_url}/v1")
    
    def generate(self, user_query: str, system_prompt: str) -> str:
        """生成文本响应"""
        payload = self._build_payload(user_query, system_prompt)
        
        try:
            response = self._make_request(payload)
            return self._extract_response(response)
        except Exception as e:
            logger.error(f"vLLM generation failed: {e}")
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
            "top_k": self.top_k,
            "stream": False,
        }
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送HTTP请求"""
        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    def _extract_response(self, response: Dict[str, Any]) -> str:
        """提取响应内容"""
        if "error" in response:
            raise RuntimeError(f"vLLM error: {response['error']}")
        
        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError("No choices in vLLM response")
        
        return choices[0]["message"]["content"].strip()
