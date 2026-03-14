"""
4B Router with Logprobs Validation
===================================

架构：规则 → 4B LLM 兜底

- 规则处理简单 query（有明确意图和参数）
- 4B LLM 处理复杂 query（意图不清或参数缺失）
- Logprobs 验证置信度（< 0.7 触发澄清）

性能目标：
- 延迟：350ms（vs 900ms with 7B reasoning）
- 准确率：85% → 90%（with logprobs fallback）
- 模型：Qwen3-4B-2507（83.75 tokens/sec）
"""

import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ToolType(Enum):
    """支持的工具类型"""
    PLAN_TRIP = "plan_trip"
    FIND_NEARBY = "find_nearby"
    GET_WEATHER = "get_weather"
    WEB_SEARCH = "web_search"
    GET_NEWS = "get_news"
    GET_STOCK = "get_stock"


@dataclass
class ToolCall:
    """工具调用（极简 JSON，无 reasoning 字段）"""
    tool: ToolType
    params: Dict[str, Any]
    confidence: float = 0.0  # Logprobs 置信度


class RuleBasedRouter:
    """
    规则路由器（处理简单 query）
    
    ==========================================
    规则优先级（从高到低，按代码顺序执行）
    ==========================================
    
    优先级 0（最高）：旅游意图关键词
    - 触发条件：query 包含 ["旅游", "旅行", "出去玩", ...]
    - 目标工具：plan_trip
    - 修复历史：修复「广州旅游」误判为 find_nearby 的 bug
    - 置信度：0.9
    
    优先级 1：目的地 + 时间
    - 触发条件：有目的地 AND 有时间表达
    - 目标工具：plan_trip
    - 置信度：0.9
    
    优先级 2：位置 + 类别
    - 触发条件：有位置 AND 有类别关键词
    - 目标工具：find_nearby
    - 注意：优先级低于旅游意图，避免冲突
    - 置信度：0.9
    
    优先级 3：天气关键词
    - 触发条件：query 包含 ["天气", "温度", ...]
    - 目标工具：get_weather
    - 置信度：0.85
    
    ==========================================
    规则冲突处理
    ==========================================
    
    如果多个规则同时匹配，按优先级顺序返回第一个匹配的规则。
    
    示例冲突场景：
    - "广州旅游" 同时匹配规则0（旅游）和规则2（位置+类别）
    - 解决：规则0 优先级更高，返回 plan_trip
    
    ==========================================
    """
    
    # 目的地列表
    DESTINATIONS = ["北京", "上海", "广州", "深圳", "杭州", "西安", "成都", "南京", "苏州", "武汉", "成都"]
    
    # 旅游意图关键词（优先级高于类别关键词）
    TRIP_KEYWORDS = ["旅游", "旅行", "出去玩", "出去走走", "散散心", "出去转转", "避暑", "避寒", "度假", "度个假"]
    
    # 类别关键词映射
    CATEGORY_KEYWORDS = {
        "餐厅": ["吃", "饭", "餐", "好吃", "美食"],
        "酒店": ["住", "宾馆", "旅馆", "酒店"],
        "景点": ["景点", "玩", "游", "看"],
        "医院": ["医院", "医生", "看病"],
        "银行": ["银行", "取钱"],
        "超市": ["超市", "买", "购物"],
    }
    
    @staticmethod
    def try_route(query: str) -> Optional[ToolCall]:
        """
        尝试用规则路由
        
        规则按优先级顺序执行（0 → 1 → 2 → 3）
        先匹配到的规则优先返回
        
        如果规则能确定意图和必需参数，返回 ToolCall
        否则返回 None，交给 LLM 处理
        """
        
        # ========== 排除法：纯闲聊检测 ==========
        # 只有当query明确是纯闲聊时才返回None
        # 纯闲聊特征：包含明确的闲聊词汇（如"无聊"、"陪聊"等）
        
        casual_chat_keywords = [
            "无聊", "陪我", "陪聊", "闲聊", "扯淡", "吹牛", "讲笑话", "唱歌", "跳舞",
            "玩游戏", "成语接龙", "你好", "你是谁", "你叫什么", "你的功能", "你能做什么"
        ]
        
        # 如果包含纯闲聊词汇，返回None
        if any(kw in query for kw in casual_chat_keywords):
            return None  # 表示纯闲聊，不需要工具
        
        # 否则，继续用规则路由（不在这里提前返回）
        # ========== 规则 0：旅游意图关键词（优先级最高）==========
        # 修复历史：修复「广州旅游」误判为 find_nearby 的 bug
        if any(kw in query for kw in RuleBasedRouter.TRIP_KEYWORDS):
            destination = RuleBasedRouter._extract_destination(query)
            return ToolCall(
                tool=ToolType.PLAN_TRIP,
                params={"destination": destination} if destination else {},
                confidence=0.9
            )
        
        # ========== 规则 1：目的地 + 时间 ==========
        destination = RuleBasedRouter._extract_destination(query)
        if destination and RuleBasedRouter._has_time(query):
            return ToolCall(
                tool=ToolType.PLAN_TRIP,
                params={"destination": destination},
                confidence=0.9
            )
        
        # ========== 规则 2：位置 + 类别 ==========
        # 注意：此规则优先级低于规则0，避免「广州旅游」误判
        location = RuleBasedRouter._extract_destination(query)  # 位置和目的地用同一个列表
        category = RuleBasedRouter._extract_category(query)
        
        # 支持隐式位置词（附近/周边）
        has_implicit_location = any(kw in query for kw in ["附近", "周边", "这里", "这附近"])
        
        if (location or has_implicit_location) and category:
            return ToolCall(
                tool=ToolType.FIND_NEARBY,
                params={"city": location if location else "", "category": category},
                confidence=0.9
            )
        
        # ========== 规则 3：天气关键词 ==========
        if any(kw in query for kw in ["天气", "温度", "下雨", "晴天", "风"]):
            location = RuleBasedRouter._extract_destination(query)
            # Always route to get_weather; let the planner handle missing city via clarify.
            return ToolCall(
                tool=ToolType.GET_WEATHER,
                params={"location": location or ""},
                confidence=0.85
            )
        
        # ========== 规则 4：新闻关键词 ==========
        # 强新闻词（单独出现即可判定为新闻）
        strong_news_keywords = [
            "新闻", "热点", "热搜", "大事", "发生了什么", "国际局势",
            "爆料", "曝光", "揭露", "披露", "泄露", "内幕"
        ]
        
        # 弱新闻词（需要组合判断）
        weak_news_keywords = [
            "秘密", "密谋", "行动", "计划", "阴谋", "策划", "部署",
            "美国", "以色列", "中东", "战争", "冲突", "制裁", "谈判",
            "真相", "最近", "近期", "今天", "昨天", "本周", "这周", "当前", "消息", "最新"
        ]
        
        # 排除词（包含这些词时不是新闻，除非同时包含强新闻词）
        # 只排除明确的股票指数查询和八卦
        exclude_keywords = ["A股今天", "港股今天", "美股今天", "指数今天", "八卦"]
        
        # 检查强新闻词
        has_strong_news = any(kw in query for kw in strong_news_keywords)
        
        # 检查排除词
        has_exclude = any(kw in query for kw in exclude_keywords)
        
        # 如果有强新闻词，即使有排除词也算新闻
        if has_strong_news:
            return ToolCall(
                tool=ToolType.GET_NEWS,
                params={"query": query},
                confidence=0.85
            )
        
        # 如果有排除词且没有强新闻词，不是新闻
        if has_exclude:
            pass  # 不是新闻，继续检查其他规则
        # 检查弱新闻词组合（至少2个）
        elif sum(1 for kw in weak_news_keywords if kw in query) >= 2:
            return ToolCall(
                tool=ToolType.GET_NEWS,
                params={"query": query},
                confidence=0.85
            )
        
        # 规则无法处理，交给 LLM
        return None
    
    @staticmethod
    def _extract_destination(query: str) -> Optional[str]:
        """提取目的地"""
        for dest in RuleBasedRouter.DESTINATIONS:
            if dest in query:
                return dest
        return None
    
    @staticmethod
    def _extract_category(query: str) -> Optional[str]:
        """提取类别"""
        for category, keywords in RuleBasedRouter.CATEGORY_KEYWORDS.items():
            if any(kw in query for kw in keywords):
                return category
        return None
    
    @staticmethod
    def _has_time(query: str) -> bool:
        """检查是否有时间信息"""
        time_patterns = [
            r"\d+天", r"\d+日", r"一周", r"两周", r"一个月",
            r"\d+ days", r"\d+ weeks"
        ]
        return any(re.search(pattern, query) for pattern in time_patterns)


class LogprobsValidator:
    """
    Logprobs 置信度验证
    
    从模型的 logprobs 输出提取置信度
    阈值：0.7（低于此值触发澄清）
    
    P0 修复：不再使用硬编码 0.85，改为基于语义的启发式评分
    """
    
    @staticmethod
    def extract_confidence(response: str, query: str = "", logprobs: Optional[Dict] = None) -> float:
        """
        从 logprobs 提取置信度
        
        如果没有 logprobs，使用语义启发式评分（不再是硬编码 0.85）
        
        Args:
            response: LLM 响应
            query: 用户查询（用于语义验证）
            logprobs: Logprobs 数据（如果可用）
        """
        
        if logprobs is None:
            # P0 修复：语义启发式评分
            try:
                data = json.loads(response)
                tool = data.get("tool", "")
                params = data.get("params", {})
                
                # 检查 1：极短查询（≤2 字）降低置信度
                if len(query.strip()) <= 2:
                    return 0.4
                
                # 检查 2：必需参数是否存在
                required_params = {
                    "plan_trip": ["destination"],
                    "find_nearby": ["city", "category"],
                    "get_weather": ["location"],
                    "web_search": ["query"],
                    "get_news": ["query"],
                    "get_stock": ["symbol"]
                }
                
                if tool in required_params:
                    missing = [p for p in required_params[tool] if not params.get(p)]
                    if missing:
                        return 0.5  # 缺少必需参数
                
                # 检查 3：参数值是否为空
                if params and all(not v for v in params.values()):
                    return 0.6  # 参数全空
                
                # 检查 4：工具选择是否合理（基于关键词）
                tool_keywords = {
                    "plan_trip": ["旅游", "行程", "规划", "去", "玩"],
                    "find_nearby": ["附近", "找", "哪里有", "推荐"],
                    "get_weather": ["天气", "温度", "下雨", "晴", "带伞"],
                    "get_news": ["新闻", "大事", "消息"],
                    "get_stock": ["股票", "股价", "公司表现"]
                }
                
                if tool in tool_keywords:
                    has_keyword = any(kw in query for kw in tool_keywords[tool])
                    if not has_keyword and tool != "web_search":
                        return 0.65  # 工具选择可疑
                
                # 所有检查通过
                return 0.85
                
            except json.JSONDecodeError:
                return 0.3  # 格式错误 = 低置信度
        
        # 使用 logprobs（如果可用）
        if "top_logprobs" in logprobs:
            probs = []
            for token_logprobs in logprobs["top_logprobs"]:
                if token_logprobs:
                    max_prob = max(token_logprobs.values())
                    probs.append(max_prob)
            
            if probs:
                avg_prob = sum(probs) / len(probs)
                confidence = min(1.0, max(0.0, avg_prob))
                return confidence
        
        return 0.5
    
    @staticmethod
    def should_fallback(confidence: float, threshold: float = 0.7) -> bool:
        """检查是否应该触发澄清"""
        return confidence < threshold


class Router4BWithLogprobs:
    """
    4B Router with Logprobs Validation
    
    流程：
    1. 尝试规则路由（快速）
    2. 如果规则失败，调用 4B LLM
    3. 用 logprobs 验证 LLM 输出
    4. 如果置信度低，触发澄清
    """
    
    # 优化的系统提示词（针对 4B 模型）
    SYSTEM_PROMPT = """你是意图识别系统。分析用户 query，输出工具调用的 JSON。

【支持的工具】
plan_trip    旅游行程规划     参数: destination（目的地，可为空）
find_nearby  查找附近地点     参数: city（城市）, category（类别）
get_weather  天气查询         参数: location（位置，可为空）
get_news     新闻资讯         参数: query（查询词）
get_stock    股票行情         参数: symbol（公司名或股票代码）
web_search   通用搜索（兜底） 参数: query（查询词）

【判断逻辑——按顺序检查】
步骤1 有无旅游/出行意图？
- 含"旅游/旅行/行程/度假/出去玩/散散心/避暑/避寒"等 → plan_trip
- 目的地+天数 → plan_trip

步骤2 有无附近/位置+类别意图？
- 含"附近/周边/周围"+"餐厅/酒店/加油站/景点/停车场"等 → find_nearby
- 城市名+地点类别 → find_nearby，city=城市名

步骤3 有无天气意图？
- 含"天气/温度/下雨/冷/热/带伞/穿什么" → get_weather
- location 能提取则填，提取不到则留空

步骤4 有无新闻意图？
- 含"新闻/热点/热搜/大事/消息/发生了什么" → get_news

步骤5 有无股票意图？
- 含"股票/股价/涨跌/行情/市值" + 公司名 → get_stock

步骤6 以上都不符合 → web_search，query=原始用户输入

【特殊情况处理】
- 参数缺失时：仍然输出工具名，缺失的参数留空字符串""
- 意图冲突时：旅游意图 > 附近意图（"广州旅游" → plan_trip 而非 find_nearby）
- query 极短（单字/两字）：输出对应工具但参数留空
- 含"搜/查/帮我找"等动词前缀：去掉前缀再判断意图

【输出格式】严格 JSON，不输出任何其他内容
{"tool": "...", "params": {"key": "value"}}

【示例】
"北京3天旅游"          → {"tool":"plan_trip","params":{"destination":"北京"}}
  理由：含旅游关键词+目的地 → plan_trip

"我想去一个有山有水的地方" → {"tool":"plan_trip","params":{"destination":""}}
  理由：含出行意图但无具体目的地 → plan_trip，destination留空

"散散心"               → {"tool":"plan_trip","params":{"destination":""}}
  理由：含避暑/散心等出行意图 → plan_trip

"附近有什么好吃的"      → {"tool":"find_nearby","params":{"city":"","category":"餐厅"}}
  理由：含附近+餐厅类别 → find_nearby

"上海附近的酒店"        → {"tool":"find_nearby","params":{"city":"上海","category":"酒店"}}
  理由：城市+类别 → find_nearby

"广州旅游"             → {"tool":"plan_trip","params":{"destination":"广州"}}
  理由：旅游意图优先于位置意图 → plan_trip

"明天要带伞吗"          → {"tool":"get_weather","params":{"location":""}}
  理由：含天气意图但无位置 → get_weather

"成都天气"             → {"tool":"get_weather","params":{"location":"成都"}}
  理由：城市+天气 → get_weather

"最近有什么大事"        → {"tool":"get_news","params":{"query":"最近大事"}}
  理由：含新闻/大事关键词 → get_news

"茅台股价多少"          → {"tool":"get_stock","params":{"symbol":"茅台"}}
  理由：含股价+公司名 → get_stock

"A股今天怎么样"         → {"tool":"web_search","params":{"query":"A股今天行情"}}
  理由：股票指数查询属于知识查询 → web_search

"帮我搜下去西藏旅游注意什么" → {"tool":"web_search","params":{"query":"去西藏旅游注意事项"}}
  理由：旅游知识查询（非行程规划）→ web_search

"GAI是谁"             → {"tool":"web_search","params":{"query":"GAI说唱歌手"}}
  理由：媒体艺人信息查询（知识查询）→ web_search

"郭富城的老婆是谁"      → {"tool":"web_search","params":{"query":"郭富城老婆"}}
  理由：明星个人信息查询（知识查询）→ web_search

"张震岳的代表作是什么"   → {"tool":"web_search","params":{"query":"张震岳代表作"}}
  理由：艺人作品信息查询（知识查询）→ web_search

"飞驰人生3剧情大概是啥" → {"tool":"web_search","params":{"query":"飞驰人生3剧情"}}
  理由：电影剧情信息查询（知识查询）→ web_search

"天气"                → {"tool":"get_weather","params":{"location":""}}
  理由：单字天气意图 → get_weather，location留空
"""
    
    def __init__(self, llm_client=None):
        """
        初始化 4B Router
        
        Args:
            llm_client: LLM 客户端（用于兜底）
        """
        self.llm_client = llm_client
        self.rule_router = RuleBasedRouter()
        self.validator = LogprobsValidator()
    
    def route(self, query: str, prev_user_msg: str = "") -> Dict[str, Any]:
        """
        路由查询

        Args:
            query: 当前用户查询
            prev_user_msg: 上一轮用户原话（帮助 LLM 理解指代/省略，规则层不用）

        Returns:
        {
            "success": bool,
            "tool": str,
            "params": dict,
            "confidence": float,
            "needs_clarification": bool,
            "error": str (if any)
        }
        """

        try:
            # 步骤1：尝试规则路由（规则层不传 history，纯 keyword 匹配）
            rule_result = self.rule_router.try_route(query)
            
            if rule_result:
                # 规则成功，直接返回
                return {
                    "success": True,
                    "tool": rule_result.tool.value,
                    "params": rule_result.params,
                    "confidence": rule_result.confidence,
                    "needs_clarification": False,
                    "source": "rule"
                }
            
            # 步骤1.5：检查是否为纯闲聊（规则返回None且不包含工具关键词）
            # 这里rule_result为None，说明规则层判断为纯闲聊
            # 返回特殊标记，让chat_flow直接用LLM回复
            casual_chat_keywords = [
                "无聊", "陪我", "陪聊", "闲聊", "扯淡", "吹牛", "讲笑话", "唱歌", "跳舞",
                "玩游戏", "成语接龙", "你好", "你是谁", "你叫什么", "你的功能", "你能做什么"
            ]
            if any(kw in query for kw in casual_chat_keywords):
                # 纯闲聊，返回None作为tool标记
                return {
                    "success": True,
                    "tool": None,  # None表示纯闲聊，不需要工具
                    "params": {},
                    "confidence": 1.0,
                    "needs_clarification": False,
                    "source": "casual_chat"
                }
            
            # 步骤2：规则失败，调用 LLM
            if not self.llm_client:
                # 没有 LLM 客户端，返回失败
                return {
                    "success": False,
                    "tool": "web_search",
                    "params": {"query": query},
                    "confidence": 0.0,
                    "needs_clarification": False,
                    "error": "No LLM client available",
                    "source": "none"
                }
            
            llm_result = self._route_with_llm(query, prev_user_msg=prev_user_msg)
            return llm_result
        
        except Exception as e:
            return {
                "success": False,
                "tool": "web_search",
                "params": {"query": query},
                "confidence": 0.0,
                "needs_clarification": False,
                "error": str(e),
                "source": "error"
            }
    
    def _route_with_llm(self, query: str, prev_user_msg: str = "") -> Dict[str, Any]:
        """
        用 LLM 路由（兜底）

        使用 logprobs 验证置信度。
        prev_user_msg 提供上一轮用户原话，帮助 4B 理解指代/省略。
        """

        try:
            # 拼接上一轮用户原话作为短上下文（不带 intent，不带助手回复）
            if prev_user_msg:
                user_message = f"[上文：{prev_user_msg}] {query}"
            else:
                user_message = query

            # 调用 LLM
            response = self.llm_client.call(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=user_message,
                response_format="json",
                temperature=0.2,  # 低温度提高一致性
                max_tokens=150,   # 极简输出
            )
            
            # 解析响应
            tool_call = self._parse_response(response)
            
            if tool_call is None:
                # 这个分支理论上不会到达（parse 失败会返回 web_search 兜底）
                return {
                    "success": False,
                    "tool": "web_search",
                    "params": {"query": query},
                    "confidence": 0.0,
                    "needs_clarification": False,
                    "error": "Failed to parse LLM response",
                    "source": "llm_parse_error"
                }
            
            # 提取置信度（传入 query 用于语义验证）
            confidence = self.validator.extract_confidence(response, query=query)
            
            # 检查是否应该触发澄清
            if self.validator.should_fallback(confidence):
                return {
                    "success": False,
                    "tool": tool_call.tool.value,
                    "params": tool_call.params,
                    "confidence": confidence,
                    "needs_clarification": True,
                    "error": f"Low confidence ({confidence:.2f})",
                    "source": "llm_low_confidence"
                }
            
            # 成功
            return {
                "success": True,
                "tool": tool_call.tool.value,
                "params": tool_call.params,
                "confidence": confidence,
                "needs_clarification": False,
                "source": "llm"
            }
        
        except Exception as e:
            return {
                "success": False,
                "tool": "web_search",
                "params": {"query": query},
                "confidence": 0.0,
                "needs_clarification": False,
                "error": f"LLM call failed: {str(e)}",
                "source": "llm_error"
            }
    
    def _parse_response(self, response: str) -> Optional[ToolCall]:
        """
        解析 LLM 响应
        
        处理格式错误和截断的 JSON
        增强 fallback：parse 失败时返回 web_search 兜底
        """
        
        try:
            # 尝试直接解析
            data = json.loads(response)
            return self._build_tool_call(data)
        except json.JSONDecodeError:
            # 尝试从响应中提取 JSON
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    return self._build_tool_call(data)
                except json.JSONDecodeError:
                    pass
            
            # 尝试修复截断的 JSON
            if '"tool"' in response and '"params"' not in response:
                fixed = response.rstrip() + ', "params": {}}'
                try:
                    data = json.loads(fixed)
                    return self._build_tool_call(data)
                except json.JSONDecodeError:
                    pass
            
            # P0 修复：parse 失败时返回 web_search 兜底，而不是 None
            # 这样可以避免生产环境崩溃
            return ToolCall(
                tool=ToolType.WEB_SEARCH,
                params={},
                confidence=0.0  # 低置信度标记
            )
    
    def _build_tool_call(self, data: dict) -> Optional[ToolCall]:
        """从解析的 JSON 构建 ToolCall"""
        
        try:
            tool_str = data.get("tool", "").lower()
            
            # 映射字符串到 ToolType
            tool_type = None
            for t in ToolType:
                if t.value == tool_str:
                    tool_type = t
                    break
            
            if tool_type is None:
                return None
            
            params = data.get("params", {})
            
            return ToolCall(
                tool=tool_type,
                params=params,
                confidence=0.0  # 由 validator 设置
            )
        
        except Exception:
            return None


# 示例用法
if __name__ == "__main__":
    router = Router4BWithLogprobs()
    
    test_queries = [
        "我想去北京3天",
        "北京附近有什么好吃的",
        "今天天气怎么样",
        "什么是人工智能",
    ]
    
    for query in test_queries:
        result = router.route(query)
        print(f"Query: {query}")
        print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print()
