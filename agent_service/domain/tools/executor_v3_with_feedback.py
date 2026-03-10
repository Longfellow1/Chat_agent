"""
改进的工具执行器 v3

支持：
1. 重试时注入错误反馈
2. 参数验证失败时的智能提示
3. 工具执行失败时的自动降级
4. 详细的执行日志
"""

from dataclasses import dataclass
from typing import Any, Optional, Callable
from enum import Enum

from infra.tool_clients.mcp_gateway import MCPToolGateway
from domain.tools.types import ToolResult
from domain.intents.unified_router_v2_enhanced import (
    ToolCall, ToolType, RouterResult, UnifiedRouterV2
)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    result: Optional[ToolResult] = None
    error: str = ""
    tool_used: Optional[ToolType] = None
    is_fallback: bool = False
    retry_reason: str = ""
    execution_log: list[str] = None  # 执行日志
    
    def __post_init__(self):
        if self.execution_log is None:
            self.execution_log = []


class ToolExecutorV3:
    """改进的工具执行器 v3"""
    
    def __init__(self, router: UnifiedRouterV2):
        self.gateway = MCPToolGateway()
        self.router = router
    
    def execute(
        self,
        router_result: RouterResult,
        query: str = "",
        conversation_id: str = "default",
        max_retries: int = 2
    ) -> ExecutionResult:
        """
        执行工具调用，支持智能重试
        
        Args:
            router_result: 路由结果
            query: 原始查询
            conversation_id: 对话ID
            max_retries: 最大重试次数
            
        Returns:
            ExecutionResult
        """
        log = []
        
        # 1. 检查路由是否成功
        if not router_result.success:
            log.append(f"[ERROR] 路由失败: {router_result.error}")
            return ExecutionResult(
                success=False,
                error=f"路由失败: {router_result.error}",
                execution_log=log
            )
        
        tool_call = router_result.tool_call
        log.append(f"[INFO] 识别工具: {tool_call.tool.value}, 置信度: {tool_call.confidence:.2f}")
        
        # 2. 检查是否需要澄清
        if router_result.needs_clarification:
            log.append(f"[WARN] 参数不完整: {router_result.clarification_prompt}")
            return ExecutionResult(
                success=False,
                error=router_result.clarification_prompt,
                retry_reason=router_result.clarification_prompt,
                execution_log=log
            )
        
        # 3. 检查置信度，如果低则尝试 fallback
        if not tool_call.is_confident() and router_result.fallback_tool:
            log.append(f"[WARN] 置信度低 ({tool_call.confidence:.2f}), 降级到 {router_result.fallback_tool.value}")
            return self._execute_with_fallback(
                tool_call,
                router_result.fallback_tool,
                query,
                log
            )
        
        # 4. 执行工具（支持重试）
        return self._execute_with_retry(
            tool_call,
            query,
            conversation_id,
            max_retries,
            log
        )
    
    def _execute_with_retry(
        self,
        tool_call: ToolCall,
        query: str,
        conversation_id: str,
        max_retries: int,
        log: list[str]
    ) -> ExecutionResult:
        """
        执行工具，支持重试
        
        重试策略：
        1. 第一次失败 → 注入错误信息，重新路由
        2. 第二次失败 → 尝试 fallback 工具
        """
        for attempt in range(max_retries):
            log.append(f"[INFO] 执行尝试 {attempt + 1}/{max_retries}")
            
            # 执行工具
            result = self._execute_tool(tool_call, log)
            
            if result.success and result.result and result.result.ok:
                log.append(f"[SUCCESS] 工具执行成功")
                return result
            
            # 如果已经是 fallback，不再重试
            if result.is_fallback:
                log.append(f"[INFO] 已使用 fallback 工具，不再重试")
                return result
            
            # 如果是最后一次尝试，返回错误
            if attempt == max_retries - 1:
                log.append(f"[ERROR] 达到最大重试次数")
                return result
            
            # 重试：注入错误反馈，重新路由
            log.append(f"[INFO] 工具执行失败，注入错误反馈进行重试")
            
            # 构建错误信息
            error_msg = result.error or "工具执行失败"
            retry_query = f"{query}\n[上一次错误: {error_msg}]"
            
            # 重新路由（注入错误反馈）
            retry_result = self.router.route(
                retry_query,
                conversation_id=conversation_id,
                retry_count=attempt + 1
            )
            
            if not retry_result.success:
                log.append(f"[ERROR] 重试路由失败: {retry_result.error}")
                return ExecutionResult(
                    success=False,
                    error=f"重试失败: {retry_result.error}",
                    tool_used=tool_call.tool,
                    execution_log=log
                )
            
            # 更新 tool_call
            tool_call = retry_result.tool_call
            log.append(f"[INFO] 重试路由成功，新工具: {tool_call.tool.value}")
        
        return result
    
    def _execute_tool(self, tool_call: ToolCall, log: list[str]) -> ExecutionResult:
        """执行单个工具"""
        try:
            # 转换工具名称
            tool_name = self._convert_tool_name(tool_call.tool)
            
            log.append(f"[INFO] 调用工具: {tool_name}, 参数: {tool_call.params}")
            
            # 调用工具
            result = self.gateway.invoke(
                tool_name=tool_name,
                tool_args=tool_call.params
            )
            
            if result.ok:
                log.append(f"[SUCCESS] 工具返回成功")
            else:
                log.append(f"[ERROR] 工具返回失败: {result.error}")
            
            return ExecutionResult(
                success=result.ok,
                result=result,
                tool_used=tool_call.tool,
                execution_log=log
            )
            
        except Exception as e:
            error_msg = f"工具执行异常: {str(e)}"
            log.append(f"[ERROR] {error_msg}")
            
            return ExecutionResult(
                success=False,
                error=error_msg,
                tool_used=tool_call.tool,
                execution_log=log
            )
    
    def _execute_with_fallback(
        self,
        primary_tool_call: ToolCall,
        fallback_tool: ToolType,
        query: str,
        log: list[str]
    ) -> ExecutionResult:
        """
        使用 fallback 工具执行
        
        当主工具置信度低时，尝试 fallback 工具
        """
        # 构建 fallback 工具调用
        fallback_call = ToolCall(
            tool=fallback_tool,
            params=self._convert_params(primary_tool_call.params, fallback_tool),
            confidence=0.5,
            reasoning=f"主工具置信度低({primary_tool_call.confidence:.2f})，降级到{fallback_tool.value}"
        )
        
        log.append(f"[INFO] 使用 fallback 工具: {fallback_tool.value}")
        
        # 执行 fallback 工具
        result = self._execute_tool(fallback_call, log)
        result.is_fallback = True
        
        return result
    
    def _convert_tool_name(self, tool_type: ToolType) -> str:
        """将 ToolType 转换为 MCP 工具名称"""
        mapping = {
            ToolType.PLAN_TRIP: "plan_trip",
            ToolType.FIND_NEARBY: "find_nearby",
            ToolType.WEB_SEARCH: "web_search",
            ToolType.GET_WEATHER: "get_weather",
            ToolType.GET_NEWS: "get_news",
            ToolType.GET_STOCK: "get_stock",
            ToolType.ENCYCLOPEDIA: "encyclopedia",
        }
        return mapping.get(tool_type, "web_search")
    
    def _convert_params(
        self,
        params: dict[str, Any],
        target_tool: ToolType
    ) -> dict[str, Any]:
        """将参数从一个工具转换为另一个工具"""
        converted = {}
        
        if target_tool == ToolType.WEB_SEARCH:
            if "destination" in params:
                converted["query"] = params["destination"]
            elif "city" in params:
                converted["query"] = params["city"]
            elif "query" in params:
                converted["query"] = params["query"]
            else:
                converted["query"] = "查询"
        
        elif target_tool == ToolType.FIND_NEARBY:
            if "city" in params:
                converted["city"] = params["city"]
            elif "destination" in params:
                converted["city"] = params["destination"]
            
            if "category" in params:
                converted["category"] = params["category"]
            else:
                converted["category"] = "景点"
        
        else:
            converted = params.copy()
        
        return converted


class ToolExecutorV3WithMonitoring(ToolExecutorV3):
    """支持监控的工具执行器"""
    
    def __init__(self, router: UnifiedRouterV2, metrics_callback: Optional[Callable] = None):
        super().__init__(router)
        self.metrics_callback = metrics_callback
    
    def execute(
        self,
        router_result: RouterResult,
        query: str = "",
        conversation_id: str = "default",
        max_retries: int = 2
    ) -> ExecutionResult:
        """执行并记录指标"""
        result = super().execute(router_result, query, conversation_id, max_retries)
        
        # 记录指标
        if self.metrics_callback:
            self.metrics_callback({
                "success": result.success,
                "tool": result.tool_used.value if result.tool_used else None,
                "is_fallback": result.is_fallback,
                "confidence": router_result.tool_call.confidence if router_result.tool_call else 0,
                "execution_log": result.execution_log
            })
        
        return result
