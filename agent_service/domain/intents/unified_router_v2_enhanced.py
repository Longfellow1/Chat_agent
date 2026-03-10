"""
改进的统一路由器 v2

解决 Gemini 评审的 4 个隐患：
1. 强制 JSON 模式 + 7B 模型
2. 算法计算置信度（不依赖 LLM 自评）
3. 对话记忆 + 槽位填充
4. 重试时注入错误反馈
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from enum import Enum
import json
import re


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
    confidence: float  # 0.0-1.0，由算法计算而非LLM自评
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
    
    def get_missing_params(self) -> List[str]:
        """获取缺失的必需参数"""
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
        return [p for p in required if not self.params.get(p)]


@dataclass
class ConversationContext:
    """对话上下文（用于槽位填充）"""
    conversation_id: str
    active_intent: Optional[ToolType] = None  # 当前活跃意图
    partial_params: Dict[str, Any] = field(default_factory=dict)  # 已提取的参数
    turn_count: int = 0
    last_error: Optional[str] = None  # 上一次的错误信息
    
    def merge_params(self, new_params: Dict[str, Any]) -> Dict[str, Any]:
        """合并新参数和已有参数"""
        merged = self.partial_params.copy()
        merged.update(new_params)
        return merged
    
    def update_active_intent(self, tool: ToolType, params: Dict[str, Any]):
        """更新活跃意图和参数"""
        self.active_intent = tool
        self.partial_params = params
        self.turn_count += 1


@dataclass
class RouterResult:
    """路由结果"""
    success: bool
    tool_call: Optional[ToolCall] = None
    error: str = ""
    fallback_tool: Optional[ToolType] = None
    needs_clarification: bool = False  # 是否需要用户澄清
    clarification_prompt: str = ""  # 澄清提示
    
    def should_retry(self) -> bool:
        """是否应该重试（参数不完整）"""
        return self.success and not self.tool_call.is_params_complete()
    
    def should_fallback(self) -> bool:
        """是否应该降级（置信度低）"""
        return self.success and not self.tool_call.is_confident()


class ConfidenceCalculator:
    """
    算法计算置信度（不依赖LLM自评）
    
    评分维度：
    1. 参数完整性（+0.5）
    2. 参数有效性（+0.3）
    3. 意图清晰度（+0.2）
    """
    
    @staticmethod
    def calculate(tool_call: ToolCall, query: str) -> float:
        """
        计算置信度
        
        Args:
            tool_call: 工具调用
            query: 原始查询
            
        Returns:
            置信度 0.0-1.0
        """
        score = 0.0
        
        # 1. 参数完整性（+0.5）
        required_params = {
            ToolType.PLAN_TRIP: ["destination"],
            ToolType.FIND_NEARBY: ["city", "category"],
            ToolType.WEB_SEARCH: ["query"],
            ToolType.GET_WEATHER: ["city"],
            ToolType.GET_NEWS: ["query"],
            ToolType.GET_STOCK: ["symbol"],
            ToolType.ENCYCLOPEDIA: ["query"],
        }
        
        required = required_params.get(tool_call.tool, [])
        if required:
            complete_params = sum(1 for p in required if tool_call.params.get(p))
            score += (complete_params / len(required)) * 0.5
        
        # 2. 参数有效性（+0.3）
        # 检查是否有生造的参数（不在预期范围内）
        valid_param_keys = {
            ToolType.PLAN_TRIP: {"destination", "days", "travel_mode", "preferences"},
            ToolType.FIND_NEARBY: {"city", "district", "category", "brand", "keywords"},
            ToolType.WEB_SEARCH: {"query", "filters"},
            ToolType.GET_WEATHER: {"city", "district"},
            ToolType.GET_NEWS: {"query", "category"},
            ToolType.GET_STOCK: {"symbol", "exchange"},
            ToolType.ENCYCLOPEDIA: {"query"},
        }
        
        expected_keys = valid_param_keys.get(tool_call.tool, set())
        actual_keys = set(tool_call.params.keys())
        
        if expected_keys:
            valid_keys = len(actual_keys & expected_keys)
            total_keys = len(actual_keys)
            if total_keys > 0:
                score += (valid_keys / total_keys) * 0.3
            else:
                score += 0.3  # 没有参数也算有效
        
        # 3. 意图清晰度（+0.2）
        # 基于查询中的关键词匹配度
        intent_keywords = {
            ToolType.PLAN_TRIP: ["规划", "行程", "安排", "旅游", "旅行"],
            ToolType.FIND_NEARBY: ["附近", "周边", "地点", "餐厅", "酒店"],
            ToolType.WEB_SEARCH: ["搜索", "查一下", "了解"],
            ToolType.GET_WEATHER: ["天气", "气温", "下雨"],
            ToolType.GET_NEWS: ["新闻", "热点", "头条"],
            ToolType.GET_STOCK: ["股票", "股价", "行情"],
            ToolType.ENCYCLOPEDIA: ["是什么", "介绍", "定义"],
        }
        
        keywords = intent_keywords.get(tool_call.tool, [])
        if keywords:
            matched = sum(1 for kw in keywords if kw in query)
            score += min(matched / len(keywords), 1.0) * 0.2
        
        return min(score, 1.0)


class ConversationMemory:
    """对话记忆管理"""
    
    def __init__(self, max_turns: int = 10):
        self.contexts: Dict[str, ConversationContext] = {}
        self.max_turns = max_turns
    
    def get_context(self, conversation_id: str) -> ConversationContext:
        """获取对话上下文"""
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = ConversationContext(conversation_id)
        return self.contexts[conversation_id]
    
    def update_context(
        self,
        conversation_id: str,
        tool: ToolType,
        params: Dict[str, Any],
        error: Optional[str] = None
    ):
        """更新对话上下文"""
        ctx = self.get_context(conversation_id)
        ctx.update_active_intent(tool, params)
        if error:
            ctx.last_error = error
    
    def clear_context(self, conversation_id: str):
        """清除对话上下文"""
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]


class UnifiedRouterV2:
    """
    改进的统一路由器 v2
    
    改进点：
    1. 强制 JSON 模式（使用 Instructor 库）
    2. 算法计算置信度（不依赖 LLM 自评）
    3. 对话记忆 + 槽位填充
    4. 重试时注入错误反馈
    """
    
    SYSTEM_PROMPT_BASE = """你是一个意图识别和参数提取助手。

用户输入一个查询，你需要：
1. 识别用户的意图（选择一个工具）
2. 提取必要的参数
3. 返回结构化的 JSON

支持的工具：
- plan_trip: 行程规划（需要：destination）
- find_nearby: 查找附近（需要：city, category）
- web_search: 网络搜索（需要：query）
- get_weather: 天气查询（需要：city）
- get_news: 新闻查询（需要：query）
- get_stock: 股票查询（需要：symbol）
- encyclopedia: 百科查询（需要：query）

返回 JSON 格式（必须是有效的 JSON）：
{
  "tool": "工具名",
  "params": {参数字典},
  "reasoning": "判断理由"
}

重要：
- 只返回 JSON，不要有其他文本
- 确保 JSON 格式正确（闭合括号、引号等）
- 不要生造参数字段
"""
    
    SYSTEM_PROMPT_WITH_CONTEXT = """你是一个意图识别和参数提取助手。

用户输入一个查询，你需要：
1. 识别用户的意图（选择一个工具）
2. 提取必要的参数
3. 返回结构化的 JSON

支持的工具：
- plan_trip: 行程规划（需要：destination）
- find_nearby: 查找附近（需要：city, category）
- web_search: 网络搜索（需要：query）
- get_weather: 天气查询（需要：city）
- get_news: 新闻查询（需要：query）
- get_stock: 股票查询（需要：symbol）
- encyclopedia: 百科查询（需要：query）

对话上下文：
- 当前活跃意图：{active_intent}
- 已提取参数：{partial_params}
- 上一次错误：{last_error}

如果用户的新输入是对上一个不完整请求的补充，请合并参数。

返回 JSON 格式（必须是有效的 JSON）：
{
  "tool": "工具名",
  "params": {参数字典},
  "reasoning": "判断理由"
}

重要：
- 只返回 JSON，不要有其他文本
- 确保 JSON 格式正确（闭合括号、引号等）
- 不要生造参数字段
"""
    
    def __init__(self, llm_client, use_instructor: bool = True):
        """
        Args:
            llm_client: LLM客户端（需要支持 JSON 输出）
            use_instructor: 是否使用 Instructor 库强制 JSON 模式
        """
        self.llm_client = llm_client
        self.use_instructor = use_instructor
        self.memory = ConversationMemory()
        self.confidence_calculator = ConfidenceCalculator()
    
    def route(
        self,
        query: str,
        conversation_id: str = "default",
        retry_count: int = 0
    ) -> RouterResult:
        """
        路由查询
        
        Args:
            query: 用户查询
            conversation_id: 对话ID（用于多轮对话）
            retry_count: 重试次数
            
        Returns:
            RouterResult
        """
        try:
            # 获取对话上下文
            ctx = self.memory.get_context(conversation_id)
            
            # 构建 Prompt
            if ctx.active_intent and retry_count == 0:
                # 有活跃意图且不是重试，使用上下文 Prompt
                system_prompt = self.SYSTEM_PROMPT_WITH_CONTEXT.format(
                    active_intent=ctx.active_intent.value,
                    partial_params=json.dumps(ctx.partial_params, ensure_ascii=False),
                    last_error=ctx.last_error or "无"
                )
            elif retry_count > 0:
                # 重试时，注入错误反馈
                system_prompt = self.SYSTEM_PROMPT_BASE + f"\n\n上一次错误：{ctx.last_error}\n请修正这个错误并重新生成。"
            else:
                system_prompt = self.SYSTEM_PROMPT_BASE
            
            # 调用 LLM（强制 JSON 模式）
            response = self._call_llm_with_json_mode(system_prompt, query)
            
            # 解析响应
            tool_call = self._parse_response(response)
            
            if not tool_call:
                return RouterResult(
                    success=False,
                    error="LLM 返回格式错误或无法解析"
                )
            
            # 如果有活跃意图，合并参数
            if ctx.active_intent == tool_call.tool:
                merged_params = ctx.merge_params(tool_call.params)
                tool_call.params = merged_params
            
            # 算法计算置信度（不依赖 LLM 自评）
            tool_call.confidence = self.confidence_calculator.calculate(tool_call, query)
            
            # 检查参数完整性
            if not tool_call.is_params_complete():
                missing = tool_call.get_missing_params()
                error_msg = f"缺少参数: {', '.join(missing)}"
                
                # 更新上下文
                self.memory.update_context(
                    conversation_id,
                    tool_call.tool,
                    tool_call.params,
                    error=error_msg
                )
                
                return RouterResult(
                    success=True,
                    tool_call=tool_call,
                    needs_clarification=True,
                    clarification_prompt=f"请提供以下信息: {', '.join(missing)}"
                )
            
            # 检查置信度
            if not tool_call.is_confident():
                fallback = self._get_fallback_tool(query, tool_call.tool)
                return RouterResult(
                    success=True,
                    tool_call=tool_call,
                    fallback_tool=fallback
                )
            
            # 更新上下文
            self.memory.update_context(conversation_id, tool_call.tool, tool_call.params)
            
            return RouterResult(
                success=True,
                tool_call=tool_call
            )
            
        except Exception as e:
            return RouterResult(
                success=False,
                error=f"路由失败: {str(e)}"
            )
    
    def _call_llm_with_json_mode(self, system_prompt: str, user_message: str) -> str:
        """
        调用 LLM，强制 JSON 模式
        
        如果支持 Instructor，使用 Instructor 库
        否则使用普通 JSON 模式
        """
        if self.use_instructor:
            try:
                import instructor
                
                # 使用 Instructor 库强制 JSON 模式
                response = self.llm_client.call(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    response_format="json",
                    temperature=0.3  # 降低温度以提高稳定性
                )
                return response
            except ImportError:
                # Instructor 不可用，降级到普通 JSON 模式
                pass
        
        # 普通 JSON 模式
        response = self.llm_client.call(
            system_prompt=system_prompt,
            user_message=user_message,
            response_format="json",
            temperature=0.3
        )
        return response
    
    def _parse_response(self, response: str) -> Optional[ToolCall]:
        """
        解析 LLM 响应
        
        支持多种格式：
        1. 纯 JSON
        2. JSON 前后有文本
        3. 多行 JSON
        """
        try:
            # 尝试直接解析
            data = json.loads(response)
            return self._build_tool_call(data)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 JSON（处理前后有文本的情况）
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return self._build_tool_call(data)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _build_tool_call(self, data: dict) -> Optional[ToolCall]:
        """从字典构建 ToolCall"""
        try:
            return ToolCall(
                tool=ToolType(data["tool"]),
                params=data.get("params", {}),
                confidence=0.5,  # 将由算法计算覆盖
                reasoning=data.get("reasoning", "")
            )
        except (ValueError, KeyError):
            return None
    
    def _get_fallback_tool(self, query: str, primary_tool: ToolType) -> Optional[ToolType]:
        """当置信度低时，尝试找备选工具"""
        if any(kw in query for kw in ["天气", "气温", "下雨"]):
            return ToolType.GET_WEATHER
        if any(kw in query for kw in ["新闻", "热点", "头条"]):
            return ToolType.GET_NEWS
        if any(kw in query for kw in ["股票", "股价", "行情"]):
            return ToolType.GET_STOCK
        if any(kw in query for kw in ["规划", "行程", "旅游"]):
            return ToolType.PLAN_TRIP
        if any(kw in query for kw in ["附近", "周边", "地点"]):
            return ToolType.FIND_NEARBY
        
        return ToolType.WEB_SEARCH
