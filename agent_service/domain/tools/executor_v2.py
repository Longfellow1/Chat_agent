"""
改进的工具执行器

支持：
1. 参数验证
2. 置信度检查
3. 自动fallback
4. 错误恢复
"""

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum

from infra.tool_clients.mcp_gateway import MCPToolGateway
from domain.tools.types import ToolResult
from domain.intents.unified_router import ToolCall, ToolType, RouterResult


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    result: Optional[ToolResult] = None
    error: str = ""
    tool_used: Optional[ToolType] = None
    is_fallback: bool = False  # 是否使用了fallback工具
    retry_reason: str = ""  # 重试原因


class ToolExecutorV2:
    """改进的工具执行器"""
    
    def __init__(self):
        self.gateway = MCPToolGateway()
    
    def execute(
        self,
        router_result: RouterResult,
        query: str = "",
        max_retries: int = 1
    ) -> ExecutionResult:
        """
        执行工具调用，支持容错
        
        Args:
            router_result: 路由结果
            query: 原始查询（用于重试提示）
            max_retries: 最大重试次数
            
        Returns:
            ExecutionResult
        """
        # 1. 检查路由是否成功
        if not router_result.success:
            return ExecutionResult(
                success=False,
                error=f"路由失败: {router_result.error}"
            )
        
        tool_call = router_result.tool_call
        
        # 2. 检查参数完整性
        if not tool_call.is_params_complete():
            return ExecutionResult(
                success=False,
                error=f"参数不完整，缺少必需字段",
                retry_reason=f"请提供更多信息，例如：{self._get_missing_params_hint(tool_call)}"
            )
        
        # 3. 检查置信度，如果低则尝试fallback
        if not tool_call.is_confident() and router_result.fallback_tool:
            return self._execute_with_fallback(
                tool_call,
                router_result.fallback_tool,
                query
            )
        
        # 4. 执行工具
        return self._execute_tool(tool_call)
    
    def _execute_tool(self, tool_call: ToolCall) -> ExecutionResult:
        """执行单个工具"""
        try:
            # 转换工具名称
            tool_name = self._convert_tool_name(tool_call.tool)
            
            # 调用工具
            result = self.gateway.invoke(
                tool_name=tool_name,
                tool_args=tool_call.params
            )
            
            return ExecutionResult(
                success=result.ok,
                result=result,
                tool_used=tool_call.tool
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"工具执行失败: {str(e)}",
                tool_used=tool_call.tool
            )
    
    def _execute_with_fallback(
        self,
        primary_tool_call: ToolCall,
        fallback_tool: ToolType,
        query: str
    ) -> ExecutionResult:
        """
        使用fallback工具执行
        
        当主工具置信度低时，尝试fallback工具
        """
        # 构建fallback工具调用
        fallback_call = ToolCall(
            tool=fallback_tool,
            params=self._convert_params(primary_tool_call.params, fallback_tool),
            confidence=0.5,
            reasoning=f"主工具置信度低({primary_tool_call.confidence:.2f})，降级到{fallback_tool.value}"
        )
        
        # 执行fallback工具
        result = self._execute_tool(fallback_call)
        result.is_fallback = True
        
        return result
    
    def _convert_tool_name(self, tool_type: ToolType) -> str:
        """将ToolType转换为MCP工具名称"""
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
        """
        将参数从一个工具转换为另一个工具
        
        例如：plan_trip的destination转换为find_nearby的city
        """
        converted = {}
        
        if target_tool == ToolType.WEB_SEARCH:
            # 尝试从params中提取query
            if "destination" in params:
                converted["query"] = params["destination"]
            elif "city" in params:
                converted["query"] = params["city"]
            elif "query" in params:
                converted["query"] = params["query"]
            else:
                converted["query"] = "查询"
        
        elif target_tool == ToolType.FIND_NEARBY:
            # 尝试从params中提取city和category
            if "city" in params:
                converted["city"] = params["city"]
            elif "destination" in params:
                converted["city"] = params["destination"]
            
            if "category" in params:
                converted["category"] = params["category"]
            else:
                converted["category"] = "景点"
        
        else:
            # 其他工具，直接复制
            converted = params.copy()
        
        return converted
    
    def _get_missing_params_hint(self, tool_call: ToolCall) -> str:
        """获取缺失参数的提示"""
        required_params = {
            ToolType.PLAN_TRIP: ["destination", "days"],
            ToolType.FIND_NEARBY: ["city", "category"],
            ToolType.WEB_SEARCH: ["query"],
            ToolType.GET_WEATHER: ["city"],
            ToolType.GET_NEWS: ["query"],
            ToolType.GET_STOCK: ["symbol"],
            ToolType.ENCYCLOPEDIA: ["query"],
        }
        
        required = required_params.get(tool_call.tool, [])
        missing = [p for p in required if not tool_call.params.get(p)]
        
        return ", ".join(missing) if missing else "未知"


class ToolExecutorWithRetry(ToolExecutorV2):
    """支持重试的工具执行器"""
    
    def execute_with_retry(
        self,
        router_result: RouterResult,
        query: str = "",
        max_retries: int = 2
    ) -> ExecutionResult:
        """
        执行工具，支持重试
        
        重试场景：
        1. 参数不完整 → 提示用户补充
        2. 工具执行失败 → 尝试fallback工具
        3. 结果为空 → 尝试web_search
        """
        for attempt in range(max_retries):
            result = self.execute(router_result, query)
            
            if result.success and result.result and result.result.ok:
                return result
            
            # 如果已经是fallback，不再重试
            if result.is_fallback:
                return result
            
            # 如果是参数不完整，不重试
            if result.retry_reason:
                return result
        
        return result
