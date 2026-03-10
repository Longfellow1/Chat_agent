"""
统一意图识别 + 参数提取

单次LLM调用，直接输出：
{
  "tool": "plan_trip",
  "params": {...},
  "confidence": 0.95,
  "reasoning": "..."
}
"""

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum


class ToolType(str, Enum):
    """支持的工具类型"""
    PLAN_TRIP = "plan_trip"
    FIND_NEARBY = "find_nearby"
    WEB_SEARCH = "web_search"
    GET_WEATHER = "get_weather"
    GET_NEWS = "get_news"
    GET_STOCK = "get_stock"
    ENCYCLOPEDIA = "encyclopedia"


@dataclass
class ToolCall:
    """LLM输出的工具调用"""
    tool: ToolType
    params: dict[str, Any]
    confidence: float  # 0.0-1.0
    reasoning: str = ""
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """判断置信度是否足够"""
        return self.confidence >= threshold
    
    def is_params_complete(self) -> bool:
        """检查参数是否完整"""
        required_params = {
            ToolType.PLAN_TRIP: ["destination"],
            ToolType.FIND_NEARBY: ["city", "category"],
            ToolType.WEB_SEARCH: ["query"],
            ToolType.GET_WEATHER: ["city"],
            ToolType.GET_NEWS: ["query"],
            ToolType.GET_STOCK: ["symbol"],
            ToolType.ENCYCLOPEDIA: ["query"],
        }
        
        required = required_params.get(self.tool, [])
        return all(self.params.get(key) for key in required)


@dataclass
class RouterResult:
    """路由结果"""
    success: bool
    tool_call: Optional[ToolCall] = None
    error: str = ""
    fallback_tool: Optional[ToolType] = None  # 低置信度时的备选工具
    
    def should_retry(self) -> bool:
        """是否应该重试（参数不完整）"""
        return self.success and not self.tool_call.is_params_complete()
    
    def should_fallback(self) -> bool:
        """是否应该降级（置信度低）"""
        return self.success and not self.tool_call.is_confident()


class UnifiedRouter:
    """
    统一路由器：单次LLM调用
    
    使用方式：
    1. 调用 route(query) 获取 RouterResult
    2. 检查 result.success
    3. 如果 result.should_fallback()，使用 result.fallback_tool
    4. 如果 result.should_retry()，提示用户补充信息
    5. 否则执行 result.tool_call
    """
    
    # LLM Prompt 模板
    SYSTEM_PROMPT = """你是一个意图识别和参数提取助手。

用户输入一个查询，你需要：
1. 识别用户的意图（选择一个工具）
2. 提取必要的参数
3. 给出置信度评分

支持的工具：
- plan_trip: 行程规划（需要：destination, days, travel_mode）
- find_nearby: 查找附近（需要：city, category）
- web_search: 网络搜索（需要：query）
- get_weather: 天气查询（需要：city）
- get_news: 新闻查询（需要：query）
- get_stock: 股票查询（需要：symbol）
- encyclopedia: 百科查询（需要：query）

返回JSON格式：
{
  "tool": "工具名",
  "params": {参数字典},
  "confidence": 0.0-1.0,
  "reasoning": "判断理由"
}

置信度标准：
- 0.9-1.0: 非常确定（明确的关键词 + 完整参数）
- 0.7-0.9: 比较确定（有相关关键词，参数基本完整）
- 0.5-0.7: 不太确定（模糊的意图，参数可能不完整）
- <0.5: 不确定（无法判断）
"""
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM客户端（需要支持JSON输出）
        """
        self.llm_client = llm_client
    
    def route(self, query: str) -> RouterResult:
        """
        单次LLM调用进行意图识别和参数提取
        
        Args:
            query: 用户查询
            
        Returns:
            RouterResult 包含工具调用或错误信息
        """
        try:
            # 调用LLM
            response = self.llm_client.call(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=f"用户查询：{query}",
                response_format="json"
            )
            
            # 解析响应
            tool_call = self._parse_response(response)
            
            if not tool_call:
                return RouterResult(
                    success=False,
                    error="LLM返回格式错误"
                )
            
            # 检查参数完整性
            if not tool_call.is_params_complete():
                return RouterResult(
                    success=True,
                    tool_call=tool_call,
                    error=f"参数不完整，缺少必需字段"
                )
            
            # 检查置信度
            if not tool_call.is_confident():
                # 尝试找备选工具
                fallback = self._get_fallback_tool(query, tool_call.tool)
                return RouterResult(
                    success=True,
                    tool_call=tool_call,
                    fallback_tool=fallback
                )
            
            return RouterResult(
                success=True,
                tool_call=tool_call
            )
            
        except Exception as e:
            return RouterResult(
                success=False,
                error=f"路由失败: {str(e)}"
            )
    
    def _parse_response(self, response: str) -> Optional[ToolCall]:
        """解析LLM响应"""
        import json
        try:
            data = json.loads(response)
            return ToolCall(
                tool=ToolType(data["tool"]),
                params=data.get("params", {}),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", "")
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return None
    
    def _get_fallback_tool(self, query: str, primary_tool: ToolType) -> Optional[ToolType]:
        """
        当置信度低时，尝试找备选工具
        
        使用规则匹配作为快速fallback
        """
        # 简单的规则匹配
        if any(kw in query for kw in ["天气", "气温", "下雨"]):
            return ToolType.GET_WEATHER
        if any(kw in query for kw in ["新闻", "热点", "头条"]):
            return ToolType.GET_NEWS
        if any(kw in query for kw in ["股票", "股价", "行情"]):
            return ToolType.GET_STOCK
        if any(kw in query for kw in ["规划", "行程", "旅游", "安排"]):
            return ToolType.PLAN_TRIP
        if any(kw in query for kw in ["附近", "周边", "地点"]):
            return ToolType.FIND_NEARBY
        
        # 默认降级到web_search
        return ToolType.WEB_SEARCH
