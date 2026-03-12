"""
7B 路由器 + UX 优化

包含：
1. 重试机制（JSON 截断防护）
2. UX 过渡态（前端友好）
3. 多轮澄清（避免重复问题）
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


@dataclass
class ClarificationContext:
    """澄清上下文"""
    tool: str
    partial_params: Dict[str, Any]
    missing_params: List[str]
    clarification_count: int = 0
    clarification_history: List[str] = field(default_factory=list)


@dataclass
class RouterResultWithUX:
    """包含 UX 信息的路由结果"""
    success: bool
    tool_call: Optional[Any] = None
    error: str = ""
    
    # UX 相关字段
    needs_clarification: bool = False
    transition_message: str = ""  # 过渡态消息
    clarification_prompt: str = ""  # 澄清提示
    clarification_suggestions: List[str] = field(default_factory=list)  # 建议按钮
    
    # 调试信息
    json_was_truncated: bool = False
    retry_count: int = 0


class UnifiedRouterV3_7BWithUX:
    """
    7B 路由器 + UX 优化
    
    包含：
    1. 重试机制（JSON 截断防护）
    2. UX 过渡态（前端友好）
    3. 多轮澄清（避免重复问题）
    """
    
    def __init__(self, llm_client, base_router):
        """
        Args:
            llm_client: LLM 客户端
            base_router: 基础路由器（UnifiedRouterV3_7BOptimized）
        """
        self.llm_client = llm_client
        self.base_router = base_router
        self.clarification_contexts: Dict[str, ClarificationContext] = {}
    
    def route_with_ux(
        self,
        query: str,
        conversation_id: str = "default",
        max_retries: int = 2
    ) -> RouterResultWithUX:
        """
        带 UX 优化的路由
        
        Args:
            query: 用户查询
            conversation_id: 对话 ID
            max_retries: 最大重试次数
            
        Returns:
            RouterResultWithUX
        """
        retry_count = 0
        json_was_truncated = False
        
        # 重试循环
        for attempt in range(max_retries):
            # 调用基础路由器
            result = self.base_router.route(query, conversation_id)
            
            if not result.get("success"):
                # 检查是否是 JSON 截断错误
                if "JSON" in result.get("error", "") or result.get("tool_call") is None:
                    json_was_truncated = True
                    retry_count += 1
                    
                    # 降低 temperature，让模型更简洁
                    if attempt < max_retries - 1:
                        self.llm_client.temperature = 0.2
                        continue
                
                # 其他错误，不重试
                return RouterResultWithUX(
                    success=False,
                    error=result.get("error", "路由失败"),
                    json_was_truncated=json_was_truncated,
                    retry_count=retry_count
                )
            
            # 路由成功
            tool_call = result.get("tool_call")
            
            # 检查是否需要澄清
            if result.get("needs_clarification"):
                return self._handle_clarification(
                    tool_call,
                    conversation_id,
                    json_was_truncated,
                    retry_count
                )
            
            # 路由成功且参数完整
            return RouterResultWithUX(
                success=True,
                tool_call=tool_call,
                json_was_truncated=json_was_truncated,
                retry_count=retry_count
            )
        
        # 重试失败
        return RouterResultWithUX(
            success=False,
            error="多次重试后仍然失败，请稍后重试",
            json_was_truncated=json_was_truncated,
            retry_count=retry_count
        )
    
    def _handle_clarification(
        self,
        tool_call: Any,
        conversation_id: str,
        json_was_truncated: bool,
        retry_count: int
    ) -> RouterResultWithUX:
        """
        处理参数澄清
        
        包含 UX 优化：
        1. 过渡态消息
        2. 澄清提示
        3. 建议按钮
        4. 避免重复问题
        """
        
        # 获取或创建澄清上下文
        if conversation_id not in self.clarification_contexts:
            ctx = ClarificationContext(
                tool=tool_call.tool.value,
                partial_params=tool_call.params,
                missing_params=tool_call.get_missing_params()
            )
            self.clarification_contexts[conversation_id] = ctx
        else:
            ctx = self.clarification_contexts[conversation_id]
            ctx.clarification_count += 1
        
        # 生成 UX 消息
        transition_message = self._generate_transition_message(tool_call)
        clarification_prompt = self._generate_clarification_prompt(ctx)
        suggestions = self._generate_suggestions(ctx)
        
        return RouterResultWithUX(
            success=True,
            tool_call=tool_call,
            needs_clarification=True,
            transition_message=transition_message,
            clarification_prompt=clarification_prompt,
            clarification_suggestions=suggestions,
            json_was_truncated=json_was_truncated,
            retry_count=retry_count
        )
    
    def _generate_transition_message(self, tool_call: Any) -> str:
        """生成过渡态消息"""
        
        tool = tool_call.tool.value
        params = tool_call.params
        
        if tool == "plan_trip":
            destination = params.get("destination", "目的地")
            return f"✨ 正在为您规划{destination}之旅..."
        
        elif tool == "find_nearby":
            city = params.get("city", "城市")
            category = params.get("category", "地点")
            return f"🔍 正在为您查找{city}附近的{category}..."
        
        elif tool == "web_search":
            query = params.get("query", "信息")
            return f"🌐 正在为您搜索{query}..."
        
        elif tool == "get_weather":
            city = params.get("city", "城市")
            return f"🌤️ 正在为您查询{city}的天气..."
        
        else:
            return "⏳ 正在处理您的请求..."
    
    def _generate_clarification_prompt(self, ctx: ClarificationContext) -> str:
        """生成澄清提示"""
        
        if ctx.clarification_count == 0:
            # 第一次问
            if ctx.tool == "plan_trip":
                destination = ctx.partial_params.get("destination", "目的地")
                return f"我已经了解到您想去{destination}。请问您想去几天呢？"
            
            elif ctx.tool == "find_nearby":
                city = ctx.partial_params.get("city", "城市")
                return f"我已经了解到您想在{city}查找。请问您想找什么呢？"
            
            else:
                missing = ", ".join(ctx.missing_params)
                return f"为了更好地为您服务，请提供以下信息：{missing}"
        
        elif ctx.clarification_count == 1:
            # 第二次问（用户没有回答）
            if ctx.tool == "plan_trip":
                destination = ctx.partial_params.get("destination", "目的地")
                return f"为了更好地为您规划行程，请告诉我您有多少天的时间去{destination}？"
            
            else:
                missing = ", ".join(ctx.missing_params)
                return f"请提供以下信息以继续：{missing}"
        
        else:
            # 第三次问（放弃）
            return "我暂时无法完成您的请求。请提供更多信息或尝试其他查询。"
    
    def _generate_suggestions(self, ctx: ClarificationContext) -> List[str]:
        """生成建议按钮"""
        
        if ctx.tool == "plan_trip" and "days" in ctx.missing_params:
            if ctx.clarification_count == 0:
                return ["1天", "2天", "3天", "5天", "7天"]
            else:
                return ["1天", "2天", "3天", "5天", "7天", "10天", "14天"]
        
        elif ctx.tool == "find_nearby" and "category" in ctx.missing_params:
            return ["餐厅", "景点", "酒店", "购物", "娱乐"]
        
        else:
            return []
    
    def update_clarification_context(
        self,
        conversation_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        更新澄清上下文
        
        当用户回复澄清问题时调用
        """
        
        if conversation_id not in self.clarification_contexts:
            return {"error": "没有待澄清的问题"}
        
        ctx = self.clarification_contexts[conversation_id]
        ctx.clarification_history.append(user_response)
        
        # 这里可以添加逻辑来从用户回复中提取参数
        # 例如：从"3天"中提取 days=3
        
        return {
            "success": True,
            "context": ctx
        }
    
    def clear_clarification_context(self, conversation_id: str):
        """清除澄清上下文"""
        if conversation_id in self.clarification_contexts:
            del self.clarification_contexts[conversation_id]


# ============================================================================
# 前端集成示例
# ============================================================================

class FrontendIntegration:
    """前端集成示例"""
    
    @staticmethod
    def handle_router_result(result: RouterResultWithUX) -> Dict[str, Any]:
        """
        处理路由结果并返回前端需要的数据
        
        Returns:
            前端需要的数据结构
        """
        
        if not result.success:
            return {
                "type": "error",
                "message": result.error,
                "retry_count": result.retry_count
            }
        
        if result.needs_clarification:
            return {
                "type": "clarification",
                "transition_message": result.transition_message,
                "clarification_prompt": result.clarification_prompt,
                "suggestions": result.clarification_suggestions,
                "tool": result.tool_call.tool.value,
                "partial_params": result.tool_call.params
            }
        
        # 路由成功
        return {
            "type": "success",
            "tool": result.tool_call.tool.value,
            "params": result.tool_call.params,
            "confidence": result.tool_call.confidence
        }
    
    @staticmethod
    def render_ui(result: Dict[str, Any]) -> str:
        """
        渲染 UI
        
        Args:
            result: 路由结果
            
        Returns:
            HTML 或 React 组件
        """
        
        if result["type"] == "error":
            return f"""
            <div class="error-message">
                <p>❌ {result['message']}</p>
                <p class="hint">请稍后重试</p>
            </div>
            """
        
        elif result["type"] == "clarification":
            suggestions_html = "".join([
                f'<button class="suggestion-btn">{s}</button>'
                for s in result["suggestions"]
            ])
            
            return f"""
            <div class="clarification-container">
                <div class="transition-message">
                    <p>{result['transition_message']}</p>
                </div>
                <div class="clarification-prompt">
                    <p>{result['clarification_prompt']}</p>
                </div>
                <div class="suggestions">
                    {suggestions_html}
                </div>
            </div>
            """
        
        else:  # success
            return f"""
            <div class="success-message">
                <p>✅ 已识别为：{result['tool']}</p>
                <p class="confidence">置信度：{result['confidence']:.0%}</p>
            </div>
            """
