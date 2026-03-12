"""LLM推理源管理API"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMSourcesAPI:
    """LLM推理源管理API"""
    
    def __init__(self, manager):
        """初始化API
        
        Args:
            manager: InferenceSourceManager实例
        """
        self.manager = manager
    
    def list_sources(self) -> Dict[str, Any]:
        """列出所有推理源"""
        return {
            "status": "success",
            "data": self.manager.list_sources(),
            "current_source": self.manager.get_current_source(),
        }
    
    def get_source_info(self, source_name: str) -> Dict[str, Any]:
        """获取推理源信息"""
        info = self.manager.get_source_info(source_name)
        if not info:
            return {
                "status": "error",
                "message": f"Source not found: {source_name}",
            }
        return {
            "status": "success",
            "data": info,
        }
    
    def switch_source(self, source_name: str) -> Dict[str, Any]:
        """切换推理源"""
        success = self.manager.switch_source(source_name)
        if success:
            return {
                "status": "success",
                "message": f"Switched to {source_name}",
                "current_source": self.manager.get_current_source(),
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to switch to {source_name}",
            }
    
    def enable_source(self, source_name: str) -> Dict[str, Any]:
        """启用推理源"""
        success = self.manager.enable_source(source_name)
        if success:
            return {
                "status": "success",
                "message": f"Enabled {source_name}",
            }
        else:
            return {
                "status": "error",
                "message": f"Source not found: {source_name}",
            }
    
    def disable_source(self, source_name: str) -> Dict[str, Any]:
        """禁用推理源"""
        success = self.manager.disable_source(source_name)
        if success:
            return {
                "status": "success",
                "message": f"Disabled {source_name}",
            }
        else:
            return {
                "status": "error",
                "message": f"Source not found: {source_name}",
            }
    
    def failover(self) -> Dict[str, Any]:
        """执行故障转移"""
        success = self.manager.failover_to_next()
        if success:
            return {
                "status": "success",
                "message": "Failover successful",
                "current_source": self.manager.get_current_source(),
            }
        else:
            return {
                "status": "error",
                "message": "No available sources for failover",
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取推理源指标"""
        metrics = self.manager.get_metrics()
        return {
            "status": "success",
            "data": metrics,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取推理源状态"""
        return {
            "status": "success",
            "data": {
                "current_source": self.manager.get_current_source(),
                "circuit_breaker_state": self.manager.get_circuit_breaker_state(),
                "sources": self.manager.list_sources(),
                "metrics": self.manager.get_metrics(),
            },
        }


# Flask路由示例
def create_llm_sources_routes(app, manager):
    """创建LLM推理源管理路由"""
    api = LLMSourcesAPI(manager)
    
    @app.route('/api/llm/sources', methods=['GET'])
    def list_sources():
        """GET /api/llm/sources - 列出所有推理源"""
        return api.list_sources()
    
    @app.route('/api/llm/sources/<source_name>', methods=['GET'])
    def get_source_info(source_name):
        """GET /api/llm/sources/<source_name> - 获取推理源信息"""
        return api.get_source_info(source_name)
    
    @app.route('/api/llm/sources/<source_name>/switch', methods=['POST'])
    def switch_source(source_name):
        """POST /api/llm/sources/<source_name>/switch - 切换推理源"""
        return api.switch_source(source_name)
    
    @app.route('/api/llm/sources/<source_name>/enable', methods=['POST'])
    def enable_source(source_name):
        """POST /api/llm/sources/<source_name>/enable - 启用推理源"""
        return api.enable_source(source_name)
    
    @app.route('/api/llm/sources/<source_name>/disable', methods=['POST'])
    def disable_source(source_name):
        """POST /api/llm/sources/<source_name>/disable - 禁用推理源"""
        return api.disable_source(source_name)
    
    @app.route('/api/llm/failover', methods=['POST'])
    def failover():
        """POST /api/llm/failover - 执行故障转移"""
        return api.failover()
    
    @app.route('/api/llm/metrics', methods=['GET'])
    def get_metrics():
        """GET /api/llm/metrics - 获取推理源指标"""
        return api.get_metrics()
    
    @app.route('/api/llm/status', methods=['GET'])
    def get_status():
        """GET /api/llm/status - 获取推理源状态"""
        return api.get_status()


# FastAPI路由示例
def create_llm_sources_fastapi_routes(app, manager):
    """创建LLM推理源管理FastAPI路由"""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/api/llm", tags=["llm"])
    api = LLMSourcesAPI(manager)
    
    @router.get("/sources")
    async def list_sources():
        """列出所有推理源"""
        return api.list_sources()
    
    @router.get("/sources/{source_name}")
    async def get_source_info(source_name: str):
        """获取推理源信息"""
        return api.get_source_info(source_name)
    
    @router.post("/sources/{source_name}/switch")
    async def switch_source(source_name: str):
        """切换推理源"""
        return api.switch_source(source_name)
    
    @router.post("/sources/{source_name}/enable")
    async def enable_source(source_name: str):
        """启用推理源"""
        return api.enable_source(source_name)
    
    @router.post("/sources/{source_name}/disable")
    async def disable_source(source_name: str):
        """禁用推理源"""
        return api.disable_source(source_name)
    
    @router.post("/failover")
    async def failover():
        """执行故障转移"""
        return api.failover()
    
    @router.get("/metrics")
    async def get_metrics():
        """获取推理源指标"""
        return api.get_metrics()
    
    @router.get("/status")
    async def get_status():
        """获取推理源状态"""
        return api.get_status()
    
    app.include_router(router)
