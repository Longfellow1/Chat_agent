"""
阿里云通晓 (IQS - Information Query Service) Provider

纯数据搜索 API，返回结构化结果，不涉及大模型生成
"""
import os
import requests
from typing import Dict, Any, List, Optional

from ..provider_base import SearchProvider, ProviderConfig, ProviderResult, SearchResultData


class AliyunIQSProvider(SearchProvider):
    """阿里云通晓搜索 Provider"""
    
    API_URL = "https://cloud-iqs.aliyuncs.com/search/llm"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # 从环境变量获取 API Key
        self.api_key = os.getenv("ALIYUN_IQS_API_KEY")
        
        if not self.api_key:
            raise ValueError("ALIYUN_IQS_API_KEY environment variable is required")
    
    def execute(self, query: str, **kwargs) -> ProviderResult:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            **kwargs: 可选参数
                - num_results: 结果数量 (默认 5, 最大 10)
        """
        try:
            # 构建请求
            num_results = kwargs.get("num_results", 5)
            if num_results > 10:
                num_results = 10
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "query": query,
                "numResults": num_results,
            }
            
            # 发送请求
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 解析结果
            page_items = data.get("pageItems", [])
            scene_items = data.get("sceneItems", [])
            
            if not page_items and not scene_items:
                return ProviderResult(
                    ok=False,
                    error="No results returned",
                    provider=self.config.name,
                )
            
            # 转换为标准格式
            results = []
            for item in page_items:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("summary", ""),  # 使用 summary 作为 snippet
                    "main_text": item.get("mainText"),  # 完整正文（最多3000字符）
                    "published_date": item.get("publishedDate"),  # ISO 时间格式
                    "hostname": item.get("hostname", ""),
                })
            
            # 构建返回数据
            result_data = SearchResultData(
                text=f"Found {len(results)} results",
                raw={
                    "results": results,
                    "page_items": page_items,
                    "scene_items": scene_items,  # 垂类场景（天气、时间等）
                    "request_id": data.get("requestId"),
                }
            )
            
            return ProviderResult(
                ok=True,
                data=result_data,
                provider=self.config.name,
                metadata={
                    "result_count": len(results),
                    "has_scene_items": len(scene_items) > 0,
                    "request_id": data.get("requestId"),
                }
            )
        
        except requests.exceptions.Timeout:
            return ProviderResult(
                ok=False,
                error=f"Request timeout after {self.config.timeout}s",
                provider=self.config.name,
            )
        
        except requests.exceptions.HTTPError as e:
            return ProviderResult(
                ok=False,
                error=f"HTTP error: {e.response.status_code} - {e.response.text}",
                provider=self.config.name,
            )
        
        except Exception as e:
            return ProviderResult(
                ok=False,
                error=f"Unexpected error: {str(e)}",
                provider=self.config.name,
            )
