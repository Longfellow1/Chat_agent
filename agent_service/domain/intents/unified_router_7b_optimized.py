"""
针对 7B 模型的优化路由器

核心优化：
1. 结构化输出优化：reasoning 放在第一个字段（先思考，再开枪）
2. 工具描述的排他性设计（MECE 原则）
3. 边缘场景的 Few-Shot 提示
4. 参数提取减负（只提取决定性参数）
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import json


class ToolType(str, Enum):
    """支持的工具类型"""
    PLAN_TRIP = "plan_trip"
    FIND_NEARBY = "find_nearby"
    WEB_SEARCH = "web_search"
    GET_WEATHER = "get_weather"
    GET_NEWS = "get_news"
    GET_STOCK = "get_stock"
    ENCYCLOPEDIA = "encyclopedia"
    NEED_CLARIFICATION = "need_clarification"


@dataclass
class ToolDefinition:
    """工具定义（包含排他性描述）"""
    name: ToolType
    description: str
    boundary_description: str  # 何时不该用
    required_params: List[str]  # 决定性参数（路由阶段只提取这些）
    optional_params: List[str] = field(default_factory=list)  # 可选参数（后续阶段提取）


class ToolRegistry:
    """工具注册表（包含排他性设计）"""
    
    TOOLS = {
        ToolType.PLAN_TRIP: ToolDefinition(
            name=ToolType.PLAN_TRIP,
            description="""用于制定具体的旅行计划。
必须包含目的地和天数。
系统会为用户规划行程、推荐景点、安排交通。""",
            boundary_description="""何时不该用：
- 用户只是询问某个城市的历史、文化、天气 → 使用 web_search
- 用户只是询问某个城市有什么景点 → 使用 find_nearby
- 用户询问如何到达某个地点 → 使用 web_search（导航）
- 用户询问机票价格 → 使用 web_search
只有当用户明确表示要"规划行程"、"安排行程"、"制定计划"时，才使用本工具。""",
            required_params=["destination", "days"],
            optional_params=["travel_mode", "preferences", "budget", "has_children"]
        ),
        
        ToolType.FIND_NEARBY: ToolDefinition(
            name=ToolType.FIND_NEARBY,
            description="""用于查找某个地点附近的兴趣点（POI）。
必须包含城市和类别。
系统会返回附近的餐厅、景点、酒店等。""",
            boundary_description="""何时不该用：
- 用户要规划完整的行程 → 使用 plan_trip
- 用户询问某个地点的详细信息 → 使用 web_search
- 用户询问某个地点的评价 → 使用 web_search
只有当用户明确表示要"找附近的"、"周边有什么"时，才使用本工具。""",
            required_params=["city", "category"],
            optional_params=["district", "brand", "keywords", "sort_by"]
        ),
        
        ToolType.WEB_SEARCH: ToolDefinition(
            name=ToolType.WEB_SEARCH,
            description="""通用网络搜索工具。
用于查询任何信息：新闻、天气、价格、评价、历史、文化等。
当其他工具都不适用时，使用本工具。""",
            boundary_description="""何时不该用：
- 用户要规划行程 → 使用 plan_trip
- 用户要查找附近的地点 → 使用 find_nearby
- 用户要查询天气 → 使用 get_weather
- 用户要查询新闻 → 使用 get_news
- 用户要查询股票 → 使用 get_stock
本工具是最后的 fallback，只在其他工具都不适用时使用。""",
            required_params=["query"],
            optional_params=["filters"]
        ),
        
        ToolType.GET_WEATHER: ToolDefinition(
            name=ToolType.GET_WEATHER,
            description="""专门用于查询天气信息。
必须包含城市。
系统会返回温度、降水、风力等详细天气数据。""",
            boundary_description="""何时不该用：
- 用户询问天气对穿搭的影响 → 使用 web_search
- 用户询问天气对行程的影响 → 使用 plan_trip
只有当用户明确询问"天气"、"气温"、"下雨"时，才使用本工具。""",
            required_params=["city"],
            optional_params=["district"]
        ),
        
        ToolType.GET_NEWS: ToolDefinition(
            name=ToolType.GET_NEWS,
            description="""专门用于查询新闻信息。
必须包含查询关键词。
系统会返回最新的新闻资讯。""",
            boundary_description="""何时不该用：
- 用户询问历史事件 → 使用 web_search
- 用户询问某个话题的背景 → 使用 encyclopedia
只有当用户明确询问"新闻"、"热点"、"头条"时，才使用本工具。""",
            required_params=["query"],
            optional_params=["category"]
        ),
        
        ToolType.GET_STOCK: ToolDefinition(
            name=ToolType.GET_STOCK,
            description="""专门用于查询股票信息。
必须包含股票代码。
系统会返回股价、涨跌、行情等数据。""",
            boundary_description="""何时不该用：
- 用户询问投资建议 → 使用 web_search
- 用户询问某个公司的信息 → 使用 encyclopedia
只有当用户明确询问"股票"、"股价"、"行情"时，才使用本工具。""",
            required_params=["symbol"],
            optional_params=["exchange"]
        ),
        
        ToolType.ENCYCLOPEDIA: ToolDefinition(
            name=ToolType.ENCYCLOPEDIA,
            description="""用于查询百科知识。
用于查询概念、定义、历史、人物等基础知识。""",
            boundary_description="""何时不该用：
- 用户询问最新信息 → 使用 web_search
- 用户询问价格、评价 → 使用 web_search
只有当用户询问"是什么"、"介绍"、"定义"时，才使用本工具。""",
            required_params=["query"],
            optional_params=[]
        ),
    }
    
    @classmethod
    def get_tool_definition(cls, tool_type: ToolType) -> ToolDefinition:
        """获取工具定义"""
        return cls.TOOLS.get(tool_type)
    
    @classmethod
    def get_all_tool_descriptions(cls) -> str:
        """获取所有工具的描述（用于 Prompt）"""
        descriptions = []
        for tool_type, tool_def in cls.TOOLS.items():
            if tool_type == ToolType.NEED_CLARIFICATION:
                continue
            descriptions.append(f"""
【{tool_def.name.value}】
{tool_def.description}

{tool_def.boundary_description}
""")
        return "\n".join(descriptions)


@dataclass
class ToolCall:
    """LLM 输出的工具调用（优化后的结构）"""
    reasoning: str  # 放在第一个字段！
    tool: ToolType
    params: Dict[str, Any]
    
    def is_params_complete(self) -> bool:
        """检查决定性参数是否完整"""
        tool_def = ToolRegistry.get_tool_definition(self.tool)
        if not tool_def:
            return False
        
        required = tool_def.required_params
        return all(self.params.get(key) for key in required)


class UnifiedRouterV3_7BOptimized:
    """
    针对 7B 模型优化的路由器
    
    4 个核心优化：
    1. 结构化输出优化：reasoning 放在第一个字段
    2. 工具描述的排他性设计（MECE 原则）
    3. 边缘场景的 Few-Shot 提示
    4. 参数提取减负（只提取决定性参数）
    """
    
    # 优化后的 System Prompt（针对 7B 模型）
    SYSTEM_PROMPT = """你是一个意图识别和参数提取助手。

你的任务是：
1. 分析用户的查询
2. 识别用户的真实意图
3. 选择合适的工具
4. 提取必要的参数

【重要】你必须按照以下步骤思考：
第1步：分析用户说了什么
第2步：判断用户的真实意图
第3步：选择合适的工具
第4步：提取必要的参数

【支持的工具】
{tool_descriptions}

【返回格式】
你必须返回一个 JSON 对象，格式如下：
{{
  "reasoning": "你的分析过程（第1-3步的思考）",
  "tool": "选择的工具名称",
  "params": {{参数字典}}
}}

【重要】reasoning 字段必须放在第一个！这样你在生成 tool 时，能看到自己的分析，准确率会更高。

【边缘场景示例】
{few_shot_examples}

【参数提取规则】
- 只提取"决定性参数"（必需参数）
- 不要尝试提取所有可选参数
- 如果参数不足，在 reasoning 中说明

【重要提醒】
- 不要生造参数
- 不要选错工具
- 如果信息不足，选择 need_clarification
"""
    
    # Few-Shot 示例（边缘场景）
    FEW_SHOT_EXAMPLES = """
【示例1】意图不明确
用户说："上海"
分析：用户只说了一个城市名，没有说明意图。可能是想查天气、查景点、规划行程等。
正确做法：
{{
  "reasoning": "用户只提到了城市名'上海'，没有明确的意图。无法判断用户想要什么。",
  "tool": "need_clarification",
  "params": {{"clarification": "请告诉我您想了解上海的什么？比如：天气、景点、行程规划等"}}
}}

【示例2】跨界查询
用户说："去北京出差穿什么"
分析：这涉及两个信息：(1)去北京出差 (2)穿什么。
- 如果只是问穿什么，这是 web_search（查天气+穿搭建议）
- 不是 plan_trip（因为没有说要规划行程）
正确做法：
{{
  "reasoning": "用户询问去北京出差穿什么。这涉及天气和穿搭建议，应该用 web_search 查询。",
  "tool": "web_search",
  "params": {{"query": "北京出差穿什么 天气"}}
}}

【示例3】明确的规划意图
用户说："帮我规划一个北京3天的行程"
分析：用户明确说了"规划"、"北京"、"3天"。这是 plan_trip。
正确做法：
{{
  "reasoning": "用户明确要求规划行程，提到了目的地'北京'和天数'3天'。这是 plan_trip。",
  "tool": "plan_trip",
  "params": {{"destination": "北京", "days": 3}}
}}

【示例4】查找附近
用户说："北京附近有什么好吃的"
分析：用户要查找附近的餐厅。这是 find_nearby。
正确做法：
{{
  "reasoning": "用户询问'附近有什么好吃的'，这是查找周边兴趣点。",
  "tool": "find_nearby",
  "params": {{"city": "北京", "category": "餐厅"}}
}}

【示例5】天气查询
用户说："北京天气怎么样"
分析：用户明确询问天气。这是 get_weather。
正确做法：
{{
  "reasoning": "用户询问'天气'，这是天气查询。",
  "tool": "get_weather",
  "params": {{"city": "北京"}}
}}
"""
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client
        self.tool_registry = ToolRegistry()
    
    def route(self, query: str, conversation_id: str = "default") -> Dict[str, Any]:
        """
        路由查询
        
        Args:
            query: 用户查询
            conversation_id: 对话 ID
            
        Returns:
            路由结果
        """
        try:
            # 构建 Prompt
            system_prompt = self.SYSTEM_PROMPT.format(
                tool_descriptions=self.tool_registry.get_all_tool_descriptions(),
                few_shot_examples=self.FEW_SHOT_EXAMPLES
            )
            
            # 调用 LLM
            response = self.llm_client.call(
                system_prompt=system_prompt,
                user_message=f"用户查询：{query}",
                response_format="json",
                temperature=0.3  # 降低温度以提高稳定性
            )
            
            # 解析响应
            tool_call = self._parse_response(response)
            
            if not tool_call:
                return {
                    "success": False,
                    "error": "LLM 返回格式错误"
                }
            
            # 检查参数完整性
            if not tool_call.is_params_complete():
                tool_def = self.tool_registry.get_tool_definition(tool_call.tool)
                missing = [p for p in tool_def.required_params if not tool_call.params.get(p)]
                
                return {
                    "success": True,
                    "tool_call": tool_call,
                    "needs_clarification": True,
                    "missing_params": missing,
                    "error": f"缺少必需参数: {', '.join(missing)}"
                }
            
            return {
                "success": True,
                "tool_call": tool_call
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"路由失败: {str(e)}"
            }
    
    def _parse_response(self, response: str) -> Optional[ToolCall]:
        """解析 LLM 响应"""
        import re
        
        try:
            # 尝试直接解析
            data = json.loads(response)
            return self._build_tool_call(data)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 JSON
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
                reasoning=data.get("reasoning", ""),
                tool=ToolType(data["tool"]),
                params=data.get("params", {})
            )
        except (ValueError, KeyError):
            return None


# ============================================================================
# 参数提取减负：分阶段提取
# ============================================================================

class ParameterExtractor:
    """
    参数提取器（分阶段提取）
    
    第1阶段（路由）：只提取决定性参数
    第2阶段（执行）：提取可选参数
    """
    
    @staticmethod
    def extract_routing_params(tool_type: ToolType, query: str) -> Dict[str, Any]:
        """
        第1阶段：路由阶段只提取决定性参数
        
        这是 LLM 的唯一使命：把路指对
        """
        tool_def = ToolRegistry.get_tool_definition(tool_type)
        if not tool_def:
            return {}
        
        # 只提取决定性参数
        params = {}
        for param in tool_def.required_params:
            # 这里可以用规则或 LLM 提取
            # 为了简单起见，这里只是占位符
            pass
        
        return params
    
    @staticmethod
    def extract_execution_params(tool_type: ToolType, query: str, routing_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        第2阶段：执行阶段提取可选参数
        
        这是具体工具的使命：把细节抠对
        """
        tool_def = ToolRegistry.get_tool_definition(tool_type)
        if not tool_def:
            return routing_params
        
        # 在这个阶段，可以用轻量级的 LLM 调用或规则提取可选参数
        # 例如：交通偏好、预算等级、是否带小孩等
        
        execution_params = routing_params.copy()
        
        # 示例：对于 plan_trip，提取可选参数
        if tool_type == ToolType.PLAN_TRIP:
            # 这里可以用轻量级 LLM 调用提取
            # 但不是在路由阶段，而是在执行阶段
            pass
        
        return execution_params


# ============================================================================
# 测试示例
# ============================================================================

if __name__ == "__main__":
    # 模拟 LLM 客户端
    class MockLLMClient:
        def call(self, system_prompt: str, user_message: str, response_format: str = "json", temperature: float = 0.3) -> str:
            # 模拟 LLM 返回
            return json.dumps({
                "reasoning": "用户提到了具体的城市'北京'，并且询问了'好玩的地方'，属于寻找周边的兴趣点。",
                "tool": "find_nearby",
                "params": {"city": "北京", "category": "景点"}
            })
    
    # 初始化路由器
    llm_client = MockLLMClient()
    router = UnifiedRouterV3_7BOptimized(llm_client)
    
    # 测试
    result = router.route("北京附近有什么好玩的")
    print(json.dumps(result, indent=2, ensure_ascii=False))
