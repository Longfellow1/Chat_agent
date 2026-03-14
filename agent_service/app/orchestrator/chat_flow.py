from __future__ import annotations

import json
import os
import re
import time

from app.orchestrator.rewrite import detect_coref_signal, rewrite_query
from app.policies.post_rules import realtime_guard_reply, should_block_free_realtime_reply
from app.policies.pre_rules import (
    detect_crisis,
    detect_end_chat,
    detect_illegal_sensitive,
    detect_meaningless_noise,
    detect_boundary_response,
)
from app.policies.boundary_response import get_boundary_reply
from app.schemas.contracts import ChatRequest, ChatResponse
from domain.intents.router import RouteDecision, route_query
from domain.intents.router_4b_with_logprobs import Router4BWithLogprobs
from domain.tools.executor import ToolExecutor
from domain.tools.planner import (
    ToolPlan,
    extract_city,
    extract_nearby_keyword,
    extract_rule_tool_args,
    normalize_tool_args,
    required_slots,
)
from domain.tools.planner_v2 import build_tool_plan_v2
from infra.llm_clients.base import LLMClient
from infra.storage.session_store import InMemorySessionStore

SYSTEM_PROMPT = (
    "你是中文智能体。优先给出直接、简洁、可执行的回答。"
    "不要编造实时数据；涉及天气、新闻、股票、附近信息时，若没有工具结果请明确说明并向用户补充必要信息。"
    "对闲聊、情绪支持、日常问候，直接自然回复，不要误调用新闻或搜索工具。"
    "对医疗高风险提问（如胸痛/心梗/处方/要求确定诊断），不要给诊断与处方，明确建议尽快线下就医。"
    "对违法有害请求，明确拒绝并引导合法路径。"
)
TOOL_POST_PROMPT = (
    "你是工具结果整理助手。"
    "请基于给定的工具返回结果，生成简洁、准确、自然的中文回答。"
    "不要编造工具结果中没有的信息，不要添加未经验证的数据。"
    "如果结果里有多条候选，优先保留前三条。"
    "优先选择对用户问题最相关的关键信息（时间、地点、数值、来源）。"
)
TOOL_POST_PROMPT_STOCK = (
    "你是金融行情播报助手。"
    "请基于工具结果生成自然、通顺、简洁的中文回复，优先用2-3句完整句表达。"
    "必须保留：标的、最新价、涨跌(幅)、时间；可补充开高低收和成交量。"
    "禁止编造，不要输出与行情无关内容。"
)
TOOL_POST_PROMPT_WEATHER = (
    "你是天气播报助手。请根据用户问题和工具返回的天气数据，生成自然简洁的中文回复。\n\n"
    "### 核心要求 ###\n"
    "1. 优先直接回答用户的核心问题：\n"
    "   - '要带伞吗/会下雨吗' → 明确说是否需要带伞\n"
    "   - '适合跑步/出去玩/爬山吗' → 给出是否建议及简短理由\n"
    "   - '穿什么/穿衣建议' → 根据气温和天气给出穿衣建议\n"
    "   - '防晒/紫外线' → 根据天气状况给出建议（注明是推断非实测）\n"
    "2. 必须包含：城市、当前天气状况、气温\n"
    "3. 回复控制在3句话以内，简洁自然\n\n"
    "### 禁止行为 ###\n"
    "- 禁止编造工具中没有的数值\n"
    "- 禁止把天气现象当作指数值（如把'晴'当作紫外线指数）"
)
TOOL_POST_PROMPT_NEARBY = (
    "你是本地生活助手。请将附近搜索结果转化为自然、简洁的推荐回复。\n\n"
    "### 任务要求 ###\n"
    "1. 开头一句话直接回应用户需求（如'您附近有X家餐厅，推荐以下几家：'）\n"
    "2. 列出2-3个最优推荐，每条包含：名称、距离/地址、亮点（评分或特色）\n"
    "3. 格式自然口语化，适合语音播报\n"
    "4. 总字数控制在120字以内\n\n"
    "### 禁止行为 ###\n"
    "- 禁止编造不在结果中的商家\n"
    "- 禁止输出超过120字"
)
TOOL_POST_PROMPT_SEARCH = (
    "你是搜索结果总结助手。请将零散的搜索信息转化为简洁准确的回复。\n\n"
    "### 任务要求 ###\n"
    "1. 核心先行：第一句话直接回答用户的核心问题\n"
    "2. 信源标注：重要事实需在句末标注来源，如 [官方] 或 [可信]\n"
    "3. 去重提炼：剔除重复和无关广告信息，保留最具时效性的内容\n"
    "4. 精简表达：字数严格控制在150字内，使用简洁的句子或列表展示关键点\n"
    "5. 负面确认：如果搜索结果无法回答问题，请直说'基于现有搜索结果未能找到相关信息'，不要编造\n\n"
    "### 禁止行为 ###\n"
    "- 禁止编造搜索结果中没有的信息\n"
    "- 禁止添加未经验证的数据\n"
    "- 禁止输出超过150字的回复"
)
TOOL_POST_PROMPT_NEWS = (
    "你是新闻播报助手。请将新闻结果转化为简洁的播报。\n\n"
    "### 任务要求 ###\n"
    "1. 列表展示：用序号列出3-5条新闻，每条1句话概括\n"
    "2. 去重：如果多条新闻讲同一件事，只保留最新的一条\n"
    "3. 精简：每条新闻不超过30字，总字数不超过150字\n"
    "4. 时效性：优先展示最新的新闻\n\n"
    "### 禁止行为 ###\n"
    "- 禁止重复相同的新闻内容\n"
    "- 禁止编造新闻\n"
    "- 禁止输出超过150字"
)

ROUTER_PROMPT = (
    "你是工具路由器。根据用户问题判断是否调用工具。\n\n"
    "### 决策步骤 ###\n"
    "步骤1: 判断是否需要实时数据（天气、金融、新闻、位置、最新事实）\n"
    "步骤2: 若需要实时数据，匹配对应工具；若不需要或属于纯文本创作/闲聊，输出 reply\n"
    "步骤3: 输出严格 JSON 格式，禁止任何额外文字\n\n"
    "### 工具定义及触发场景 ###\n"
    "1. get_weather: 仅限查询实时天气、气温、空气质量或穿衣建议。若问'什么是雨'这种百科问题，选 reply\n"
    "2. get_stock: 查询股票、基金、指数的实时价格或涨跌。逻辑：名称/代码 -> get_stock\n"
    "3. get_news: 获取最新的新闻、热点快讯。若问'什么是新闻'，选 reply\n"
    "4. find_nearby: 寻找物理位置周边的POI（餐厅、酒店等）。关键词：附近、周边、最近\n"
    "5. plan_trip: 针对具体目的地的旅游方案规划\n"
    "6. web_search: 解决时效性百科、事实核查、官网链接查询。当其他工具不适用且涉及外部知识时使用\n"
    "7. reply: 适用于闲聊、自我介绍、解释概念、情感安慰、数学计算或代码编写\n\n"
    "### 负向约束（必须选 reply 的场景）###\n"
    "- 今天过得怎么样/在吗/聊聊/心情不好 -> reply（闲聊与情感支持）\n"
    "- 你是谁/你能做什么/介绍一下自己 -> reply（自我介绍）\n"
    "- 什么是XX（概念解释，非实时查询）-> reply\n"
    "- 帮我写代码/计算XX -> reply\n\n"
    "### 输出格式 ###\n"
    '{"decision_mode":"tool_call","tool_name":"get_weather","tool_args":{"city":"郑州"},"reason":"查询实时天气"}\n'
    "或\n"
    '{"decision_mode":"reply","tool_name":null,"tool_args":{},"reason":"闲聊问候"}\n\n'
    "### 补充规则 ###\n"
    "- 股票别名映射：京东->JD；贵州茅台/茅台->600519.SS；上证指数->000001.SS；深证成指->399001.SZ\n"
    "- 旅游请求应尽量从query抽取 destination（如帮我规划青岛4天旅游行程->destination=青岛）\n"
    "- 地点查询（包含附近/周边/最近的+餐厅/咖啡/便利店/医院等）必须路由到 find_nearby\n"
    "- 评分/价格/距离排序的地点查询也属于 find_nearby"
)

ALLOWED_TOOLS = {"get_weather", "get_news", "get_stock", "find_nearby", "plan_trip", "web_search"}
EXTRACTOR_PROMPTS = {
    "get_weather": (
        "你是参数提取器。只输出JSON。\n"
        '输出格式: {"tool_args":{"city":"..."}}\n'
        "从用户原句提取天气查询城市。提取不到返回空字符串。\n\n"
        "示例：\n"
        "问：'北京今天天气怎么样'\n"
        '答：{"tool_args":{"city":"北京"}}\n'
        "问：'今天穿什么'\n"
        '答：{"tool_args":{"city":""}}'
    ),
    "get_stock": (
        "你是参数提取器。只输出JSON。\n"
        '输出格式: {"tool_args":{"target":"..."}}\n'
        "优先提取股票代码/指数代码/公司简称。\n\n"
        "示例：\n"
        "问：'帮我查查百度现在的股价'\n"
        '答：{"tool_args":{"target":"BIDU"}}\n'
        "问：'茅台多少钱了'\n"
        '答：{"tool_args":{"target":"600519.SS"}}'
    ),
    "get_news": (
        "你是参数提取器。只输出JSON。"
        '输出格式: {"tool_args":{"topic":"..."}}。'
        "提取新闻主题词，提取不到可返回“今日热点”。"
    ),
    "plan_trip": (
        "你是参数提取器。只输出JSON。\n"
        '输出格式: {"tool_args":{"destination":"...","days":"..."}}\n'
        "提取目的地城市和天数，天数可空。\n\n"
        "示例：\n"
        "问：'帮我规划青岛4天旅游行程'\n"
        '答：{"tool_args":{"destination":"青岛","days":"4"}}\n'
        "问：'想去成都玩'\n"
        '答：{"tool_args":{"destination":"成都","days":""}}'
    ),
    "find_nearby": (
        "你是参数提取器。只输出JSON。\n"
        '输出格式: {"tool_args":{"keyword":"...","city":"..."}}\n'
        "提取附近检索关键词与城市，城市可空。\n\n"
        "示例：\n"
        "问：'找一下五道口附近的瑞幸'\n"
        '答：{"tool_args":{"keyword":"瑞幸咖啡","city":"北京"}}\n'
        "问：'这附近有药店吗'\n"
        '答：{"tool_args":{"keyword":"药店","city":""}}'
    ),
    "web_search": (
        "你是参数提取器。只输出JSON。\n"
        '输出格式: {"tool_args":{"query":"..."}}\n'
        "提取搜索query。\n\n"
        "示例：\n"
        "问：'OpenAI官网是什么'\n"
        '答：{"tool_args":{"query":"OpenAI官网"}}\n'
        "问：'2024年诺贝尔奖得主是谁'\n"
        '答：{"tool_args":{"query":"2024年诺贝尔奖得主"}}'
    ),
}


class ChatFlow:
    def __init__(
        self,
        llm_client: LLMClient,
        tool_executor: ToolExecutor,
        session_store: InMemorySessionStore,
    ) -> None:
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.session_store = session_store
        self.tool_post_llm = os.getenv("TOOL_POST_LLM", "true").strip().lower() == "true"
        self.tool_post_llm_timeout_sec = float(os.getenv("TOOL_POST_LLM_TIMEOUT_SEC", "18"))
        self.tool_post_llm_timeout_stock_sec = float(os.getenv("TOOL_POST_LLM_TIMEOUT_STOCK_SEC", "6"))
        self.tool_post_llm_timeout_weather_sec = float(os.getenv("TOOL_POST_LLM_TIMEOUT_WEATHER_SEC", "6"))
        self.tool_post_llm_timeout_news_sec = float(os.getenv("TOOL_POST_LLM_TIMEOUT_NEWS_SEC", "10"))  # 从30秒降到10秒
        self.tool_post_llm_timeout_search_sec = float(os.getenv("TOOL_POST_LLM_TIMEOUT_SEARCH_SEC", "5"))  # 从10秒降到5秒
        self.use_llm_router = os.getenv("USE_LLM_ROUTER", "true").strip().lower() == "true"
        self.route_timeout_sec = float(os.getenv("ROUTE_LLM_TIMEOUT_SEC", "8"))
        self.extract_timeout_sec = float(os.getenv("EXTRACT_LLM_TIMEOUT_SEC", "8"))
        self.fast_route_hint = os.getenv("FAST_ROUTE_HINT", "false").strip().lower() == "true"
        self.use_route_override = os.getenv("USE_ROUTE_OVERRIDE", "true").strip().lower() == "true"
        self.use_4b_router = os.getenv("USE_4B_ROUTER", "true").strip().lower() == "true"
        
        # 初始化4B router（如果启用）
        if self.use_4b_router:
            self.router_4b = Router4BWithLogprobs(llm_client=llm_client)
        else:
            self.router_4b = None

    def run(self, req: ChatRequest) -> ChatResponse:
        t0 = time.perf_counter()
        query = req.query.strip()

        # 0) rewrite with session context
        session_ctx: dict[str, object] = {}
        if req.session_id:
            session_ctx = self.session_store.get(req.session_id)
        rw = rewrite_query(query=query, session_ctx=session_ctx)
        effective_query = rw.effective_query or query

        # 1) pre-rules
        if detect_end_chat(query):
            resp = ChatResponse(
                query=req.query,
                effective_query=effective_query,
                rewritten=int(rw.rewritten),
                rewrite_source=rw.source,
                decision_mode="end_chat",
                final_text="好的，先聊到这里。你有需要随时叫我。",
            )
            resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
            self._persist_context(req=req, resp=resp)
            return resp

        if detect_meaningless_noise(query):
            resp = ChatResponse(
                query=req.query,
                effective_query=effective_query,
                rewritten=int(rw.rewritten),
                rewrite_source=rw.source,
                decision_mode="reject",
                risk_level="low",
                final_text="我没理解你的输入。你可以换一种更完整的说法。",
            )
            resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
            self._persist_context(req=req, resp=resp)
            return resp

        if detect_illegal_sensitive(query):
            resp = ChatResponse(
                query=req.query,
                effective_query=effective_query,
                rewritten=int(rw.rewritten),
                rewrite_source=rw.source,
                decision_mode="reject",
                risk_level="high",
                final_text="我不能帮助处理违法或危险行为相关请求。请在合法合规范围内提问。",
            )
            resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
            self._persist_context(req=req, resp=resp)
            return resp

        if detect_crisis(query):
            resp = ChatResponse(
                query=req.query,
                effective_query=effective_query,
                rewritten=int(rw.rewritten),
                rewrite_source=rw.source,
                decision_mode="reply",
                risk_level="high",
                final_text=(
                    "我听到你现在很痛苦。你并不需要一个人扛着，建议马上联系身边可信任的人，"
                    "或尽快联系当地心理援助/急救热线获取及时支持。若你有立即伤害自己的风险，请立刻拨打急救电话。"
                ),
            )
            resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
            self._persist_context(req=req, resp=resp)
            return resp

        if detect_boundary_response(query):
            boundary_reply = get_boundary_reply(query)
            resp = ChatResponse(
                query=req.query,
                effective_query=effective_query,
                rewritten=int(rw.rewritten),
                rewrite_source=rw.source,
                decision_mode="reject",
                risk_level="medium",
                final_text=boundary_reply or "这个请求超出了我的能力范围。建议咨询相关专业人士获取准确的帮助。",
            )
            resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
            self._persist_context(req=req, resp=resp)
            return resp

        # 2) route — 仅在检测到指代/省略信号时才注入上下文，避免干扰正常路由
        coref = detect_coref_signal(effective_query)
        if coref and session_ctx:
            prev_user_msg = self._get_prev_user_msg(session_ctx)
            prev_assistant_msg = self._get_prev_assistant_msg(session_ctx)
        else:
            prev_user_msg = ""
            prev_assistant_msg = ""

        t_route = time.perf_counter()
        route_source = "rule"
        llm_tool_args: dict[str, object] = {}

        # 使用4B router（如果启用）
        if self.use_4b_router and self.router_4b:
            router_result = self.router_4b.route(effective_query, prev_user_msg=prev_user_msg)
            
            # 转换为RouteDecision格式
            if router_result.get("tool") is None:
                # 纯闲聊，tool=None
                route = RouteDecision("reply", _knowledge_probs(), tool_name=None)
                route_source = "4b_casual_chat"
            elif router_result.get("success"):
                # 成功路由
                route = RouteDecision(
                    "tool_call",
                    _realtime_probs(router_result["tool"]),
                    tool_name=router_result["tool"]
                )
                llm_tool_args = router_result.get("params", {})
                route_source = router_result.get("source", "4b_router")
            else:
                # 失败，降级到reply
                route = RouteDecision("reply", _knowledge_probs(), tool_name=None)
                route_source = "4b_fallback"
        elif self.use_llm_router:
            fast_rule = route_query(effective_query)
            if self.fast_route_hint and fast_rule.decision_mode == "tool_call" and fast_rule.tool_name in ALLOWED_TOOLS:
                route = fast_rule
                route_source = "rule_fastpath"
            else:
                route, llm_tool_args = self._route_with_llm(effective_query, prev_user_msg=prev_user_msg)
                route_source = "llm_router"
                if self.use_route_override:
                    fixed = self._route_safety_override(effective_query, route)
                    if fixed.decision_mode != route.decision_mode or fixed.tool_name != route.tool_name:
                        route_source = "rule_override"
                    route = fixed
        else:
            route = route_query(effective_query)
        route_ms = int((time.perf_counter() - t_route) * 1000)

        # 2.5) 纯闲聊检测：如果tool=None，直接用LLM回复
        if route.tool_name is None:
            t1 = time.perf_counter()
            history_msgs = self._build_history_messages(session_ctx)
            if history_msgs and hasattr(self.llm_client, "generate_with_history"):
                messages = history_msgs + [{"role": "user", "content": effective_query}]
                text = self.llm_client.generate_with_history(messages=messages, system_prompt=SYSTEM_PROMPT)
            else:
                text = self.llm_client.generate(user_query=effective_query, system_prompt=SYSTEM_PROMPT)
            llm_ms = int((time.perf_counter() - t1) * 1000)
            
            resp = ChatResponse(
                query=req.query,
                effective_query=effective_query,
                rewritten=int(rw.rewritten),
                rewrite_source=rw.source,
                route_source=route_source,
                intent_probs=route.intent_probs,
                decision_mode="reply",
                final_text=text,
            )
            resp.latency_ms.llm = llm_ms
            resp.latency_ms.router = route_ms
            resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
            self._persist_context(req=req, resp=resp)
            return resp

        # 3) tool path
        if route.decision_mode == "tool_call" and route.tool_name:
            plan: ToolPlan = _build_merged_tool_plan(
                query=effective_query,
                tool_name=route.tool_name,
                llm_tool_args=llm_tool_args,
                llm_client=self.llm_client,
                timeout_sec=self.extract_timeout_sec,
                prev_assistant_msg=prev_assistant_msg,
                session_ctx=session_ctx,
            )
            if plan.missing_slots:
                resp = ChatResponse(
                    query=req.query,
                    effective_query=effective_query,
                    rewritten=int(rw.rewritten),
                    rewrite_source=rw.source,
                    route_source=route_source,
                    intent_probs=route.intent_probs,
                    decision_mode="clarify",
                    tool_name=plan.tool_name,
                    tool_args=plan.tool_args,
                    extract_source=plan.extract_source,
                    tool_status="missing_slots",
                    missing_slots=plan.missing_slots,
                    final_text=_clarify_text(plan),
                )
                resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
                resp.latency_ms.router = route_ms
                self._persist_context(req=req, resp=resp)
                return resp

            t_tool = time.perf_counter()
            tool_result = self.tool_executor.execute(plan.tool_name, plan.tool_args)
            tool_ms = int((time.perf_counter() - t_tool) * 1000)
            llm_ms = 0
            post_llm_applied = False
            post_llm_timeout = False
            final_text = tool_result.text if tool_result.ok else f"{tool_result.text}（工具：{plan.tool_name}）"
            if self.tool_post_llm and not _should_skip_post_llm(plan.tool_name, tool_result.text, tool_result.raw, query=effective_query):
                post_llm_applied = True
                t_llm = time.perf_counter()
                try:
                    post_input = _tool_post_input(
                        query=effective_query,
                        tool_name=plan.tool_name,
                        tool_args=plan.tool_args,
                        tool_text=tool_result.text,
                        tool_raw=tool_result.raw,
                        llm_client=self.llm_client,  # 传入LLM客户端
                    )
                    if hasattr(self.llm_client, "generate_with_timeout"):
                        final_text = self.llm_client.generate_with_timeout(  # type: ignore[attr-defined]
                            user_query=post_input,
                            system_prompt=_tool_post_system_prompt(plan.tool_name),
                            timeout_sec=self._tool_post_timeout(plan.tool_name),
                        )
                    else:
                        final_text = self.llm_client.generate(
                            user_query=post_input,
                            system_prompt=_tool_post_system_prompt(plan.tool_name),
                        )
                except Exception:
                    post_llm_timeout = True
                    pass
                llm_ms = int((time.perf_counter() - t_llm) * 1000)

            resp = ChatResponse(
                query=req.query,
                effective_query=effective_query,
                rewritten=int(rw.rewritten),
                rewrite_source=rw.source,
                route_source=route_source,
                intent_probs=route.intent_probs,
                decision_mode="tool_call",
                tool_name=plan.tool_name,
                tool_args=plan.tool_args,
                extract_source=plan.extract_source,
                tool_status="ok" if tool_result.ok else "fallback_or_error",
                tool_provider=_infer_tool_provider(tool_result.raw),
                tool_error=tool_result.error,
                fallback_chain=_infer_fallback_chain(tool_result.raw),
                result_quality=_infer_result_quality(tool_result, route_source),
                post_llm_applied=post_llm_applied,
                post_llm_timeout=post_llm_timeout,
                final_text=final_text,
            )
            resp.latency_ms.llm = llm_ms
            resp.latency_ms.router = route_ms
            resp.latency_ms.tools = tool_ms
            resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
            self._persist_context(req=req, resp=resp)
            return resp

        # 4) llm fallback
        t1 = time.perf_counter()
        history_msgs = self._build_history_messages(session_ctx)
        if history_msgs and hasattr(self.llm_client, "generate_with_history"):
            messages = history_msgs + [{"role": "user", "content": effective_query}]
            text = self.llm_client.generate_with_history(messages=messages, system_prompt=SYSTEM_PROMPT)
        else:
            text = self.llm_client.generate(user_query=effective_query, system_prompt=SYSTEM_PROMPT)
        llm_ms = int((time.perf_counter() - t1) * 1000)

        # 5) post-rules anti-hallucination
        if should_block_free_realtime_reply(query=effective_query, decision_mode=route.decision_mode, tool_name=route.tool_name):
            text = realtime_guard_reply(effective_query)

        resp = ChatResponse(
            query=req.query,
            effective_query=effective_query,
            rewritten=int(rw.rewritten),
            rewrite_source=rw.source,
            route_source=route_source,
            intent_probs=route.intent_probs,
            decision_mode="reply",
            final_text=text,
        )
        resp.latency_ms.llm = llm_ms
        resp.latency_ms.router = route_ms
        resp.latency_ms.total = int((time.perf_counter() - t0) * 1000)
        self._persist_context(req=req, resp=resp)
        return resp

    def _route_with_llm(self, query: str, prev_user_msg: str = "") -> tuple[RouteDecision, dict[str, object]]:
        raw = ""
        try:
            # 仅在有上下文时才注入，无上下文时保持原始格式不变
            if prev_user_msg:
                user_input = f"上一条提问：{prev_user_msg}\n当前问题：{query}"
            else:
                user_input = f"用户问题：{query}"
            if hasattr(self.llm_client, "generate_with_timeout"):
                raw = self.llm_client.generate_with_timeout(  # type: ignore[attr-defined]
                    user_query=user_input,
                    system_prompt=ROUTER_PROMPT,
                    timeout_sec=self.route_timeout_sec,
                )
            else:
                raw = self.llm_client.generate(user_query=user_input, system_prompt=ROUTER_PROMPT)

            obj = _extract_json_object(raw)
            if not isinstance(obj, dict):
                return RouteDecision("reply", _knowledge_probs(), tool_name=None), {}

            mode = str(obj.get("decision_mode", "reply")).strip().lower()
            if mode not in {"tool_call", "reply"}:
                if "tool_call" in mode:
                    mode = "tool_call"
                elif "reply" in mode:
                    mode = "reply"
                else:
                    mode = "reply"
            tool_name = obj.get("tool_name")
            if isinstance(tool_name, str):
                tool_name = tool_name.strip()
            else:
                tool_name = None
            llm_tool_args = _extract_tool_args(obj.get("tool_args"))

            if mode == "tool_call" and tool_name in ALLOWED_TOOLS:
                return RouteDecision("tool_call", _realtime_probs(), tool_name=tool_name), llm_tool_args
            return RouteDecision("reply", _knowledge_probs(), tool_name=None), {}
        except Exception:
            return RouteDecision("reply", _knowledge_probs(), tool_name=None), {}

    def _route_safety_override(self, query: str, llm_route: RouteDecision) -> RouteDecision:
        # Keep LLM as primary decider; only correct obvious realtime misses or wrong tool choices.
        fallback = route_query(query)
        
        # Case 1: LLM said reply, but rule says tool_call (original logic)
        if llm_route.decision_mode == "reply" and fallback.decision_mode == "tool_call" and fallback.tool_name in ALLOWED_TOOLS:
            return fallback
        
        # Case 2: Both say tool_call, but different tools - use rule if it has higher confidence
        if (llm_route.decision_mode == "tool_call" and fallback.decision_mode == "tool_call" 
            and llm_route.tool_name != fallback.tool_name):
            # If rule-based router has strong signal (web_search with landmark query), trust it
            if fallback.tool_name == "web_search":
                q = query.lower()
                landmark_signals = ("天文台", "博物馆", "纪念馆", "公园", "广场", "大厦", "塔", "寺", "庙", "教堂")
                if any(k in q for k in landmark_signals):
                    return fallback
        
        return llm_route

    def _tool_post_timeout(self, tool_name: str) -> float:
        if tool_name == "get_stock":
            return self.tool_post_llm_timeout_stock_sec
        if tool_name == "get_weather":
            return self.tool_post_llm_timeout_weather_sec
        if tool_name == "get_news":
            return self.tool_post_llm_timeout_news_sec
        if tool_name in {"web_search", "find_nearby"}:
            return self.tool_post_llm_timeout_search_sec
        return self.tool_post_llm_timeout_sec

    def _persist_context(self, req: ChatRequest, resp: ChatResponse) -> None:
        if not req.session_id:
            return

        tool_args = resp.tool_args or {}
        patch: dict = {
            "last_query": req.query,
            "last_effective_query": resp.effective_query,
            "last_tool": resp.tool_name,
            "last_decision_mode": resp.decision_mode,
            "last_city": tool_args.get("city") or tool_args.get("destination") or extract_city(resp.effective_query),
            "last_topic": tool_args.get("topic") or tool_args.get("query"),
            "last_target": tool_args.get("target"),
            "last_destination": tool_args.get("destination"),
        }
        # 追加对话历史（reply/tool_call 均记录，reject/clarify 不记录）
        if resp.decision_mode in ("reply", "tool_call") and resp.final_text:
            patch["history_append"] = [
                {"role": "user", "content": req.query},
                {"role": "assistant", "content": resp.final_text},
            ]
        self.session_store.upsert(req.session_id, patch)

    # ------------------------------------------------------------------
    # History / context helpers
    # ------------------------------------------------------------------

    _HISTORY_MAX_TURNS = 3          # 回复生成用 3 轮
    _HISTORY_ASSISTANT_TRUNC = 200  # 助手回复截断字符数

    def _build_history_messages(self, session_ctx: dict) -> list[dict]:
        """从 session 中取最近 3 轮历史，构造 messages 列表（不含当前 query）。

        助手回复超过 200 字符自动截断，防止小模型注意力涣散。
        """
        history: list[dict] = session_ctx.get("history", [])
        max_items = self._HISTORY_MAX_TURNS * 2  # 每轮 user+assistant
        out: list[dict] = []
        for m in history[-max_items:]:
            content = m.get("content", "")
            if m.get("role") == "assistant" and len(content) > self._HISTORY_ASSISTANT_TRUNC:
                content = content[: self._HISTORY_ASSISTANT_TRUNC]
            out.append({"role": m["role"], "content": content})
        return out

    @staticmethod
    def _get_prev_user_msg(session_ctx: dict, max_len: int = 60) -> str:
        """取上一轮用户原话（路由用，≤60 字）。"""
        history: list[dict] = session_ctx.get("history", [])
        for m in reversed(history):
            if m.get("role") == "user":
                text = m.get("content", "")
                return text[:max_len] if len(text) > max_len else text
        return ""

    @staticmethod
    def _get_prev_assistant_msg(session_ctx: dict, max_len: int = 80) -> str:
        """取上一轮助手回复（参数提取用，≤80 字，包含已解析实体）。"""
        history: list[dict] = session_ctx.get("history", [])
        for m in reversed(history):
            if m.get("role") == "assistant":
                text = m.get("content", "")
                return text[:max_len] if len(text) > max_len else text
        return ""


_SLOT_FRIENDLY_NAMES: dict[str, str] = {
    "city": "城市",
    "destination": "目的地城市",
    "target": "股票代码或名称",
    "topic": "查询关键词",
    "keyword": "搜索关键词",
    "days": "出行天数",
    "query": "搜索内容",
}


def _clarify_text(plan: ToolPlan) -> str:
    if plan.tool_name == "get_weather":
        return "你要查哪个城市的天气？例如：郑州今天天气怎么样。"
    if plan.tool_name == "plan_trip":
        return "你要去哪个城市？我可以按目的地帮你规划行程。"
    friendly = [_SLOT_FRIENDLY_NAMES.get(s, s) for s in plan.missing_slots]
    slots = "、".join(friendly)
    return f"请告诉我{slots}，我马上帮你查。"


def _tool_post_input(
    query: str,
    tool_name: str,
    tool_args: dict[str, object],
    tool_text: str,
    tool_raw: dict[str, object],
    llm_client=None,  # 添加llm_client参数
) -> str:
    # M5.3: 对 get_news 使用 Content Rewriter 清理噪声
    if tool_name == "get_news":
        try:
            from agent_service.infra.tool_clients.content_rewriter import ContentRewriter, RewriteConfig
            rewriter = ContentRewriter(
                llm_client=llm_client,  # 使用传入的LLM客户端
                config=RewriteConfig(enable_llm=True, temperature=0.3, timeout_sec=5.0)
            )
            tool_text = rewriter.rewrite_news(tool_text)
        except Exception as e:
            # 清理失败，使用原始内容
            import sys
            print(f"Content rewriter failed: {e}", file=sys.stderr)
    
    # 对 web_search 进行特殊优化：精简输入
    if tool_name == "web_search":
        # 只保留前3条结果
        results = tool_raw.get("results", [])
        if isinstance(results, list) and len(results) > 3:
            results = results[:3]
        
        # 精简每条结果
        simplified_results = []
        for r in results:
            if isinstance(r, dict):
                simplified = {
                    "title": r.get("title", "")[:100],  # 限制标题长度
                    "snippet": r.get("snippet", "")[:80],  # 限制摘要长度
                    "url": r.get("url", ""),
                }
                # 保留可信度标记
                if "credibility" in r:
                    simplified["credibility"] = r["credibility"]
                simplified_results.append(simplified)
        
        simplified_json = json.dumps(simplified_results, ensure_ascii=False)
        
        return (
            f"用户问题：{query}\n"
            f"搜索结果（前3条）：{simplified_json}\n\n"
            "请基于搜索结果生成简洁回复（150字以内）："
        )
    
    # 其他工具保持原有逻辑
    if len(tool_text) > 1200:
        tool_text = tool_text[:1200] + "...(truncated)"
    raw_json = json.dumps(tool_raw, ensure_ascii=False)
    if len(raw_json) > 3500:
        raw_json = raw_json[:3500] + "...(truncated)"
    return (
        f"用户问题：{query}\n"
        f"工具名：{tool_name}\n"
        f"工具参数：{tool_args}\n"
        f"工具返回摘要：{tool_text}\n"
        f"工具返回结构化数据(JSON)：{raw_json}\n\n"
        "请输出最终回复："
    )


def _realtime_probs(tool_name: str | None = None) -> dict[str, float]:
    """
    意图概率分布（工具调用场景）
    
    意图ID映射：
    1 = get_weather (天气查询)
    2 = get_news (新闻查询)
    3 = get_stock (股票查询)
    4 = find_nearby (附近查询)
    5 = plan_trip (旅游规划)
    6 = web_search (网络搜索)
    """
    return {"1": 0.15, "2": 0.15, "3": 0.15, "4": 0.15, "5": 0.15, "6": 0.25}


def _knowledge_probs() -> dict[str, float]:
    """
    意图概率分布（纯闲聊/LLM回复场景）
    
    意图ID映射：
    1 = get_weather (天气查询)
    2 = get_news (新闻查询)
    3 = get_stock (股票查询)
    4 = find_nearby (附近查询)
    5 = plan_trip (旅游规划)
    6 = web_search (网络搜索)
    """
    return {"1": 0.1, "2": 0.1, "3": 0.1, "4": 0.1, "5": 0.1, "6": 0.5}


def _extract_json_object(text: str) -> dict[str, object] | None:
    s = text.strip()
    if not s:
        return None
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    m = re.search(r"\{[\s\S]*\}", s)
    if not m:
        return None
    try:
        parsed = json.loads(m.group(0))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def _extract_tool_args(v: object) -> dict[str, object]:
    if not isinstance(v, dict):
        return {}
    out: dict[str, object] = {}
    for k, val in v.items():
        if not isinstance(k, str):
            continue
        if isinstance(val, (str, int, float, bool)):
            out[k] = val
    return out


def _infer_tool_provider(raw: dict[str, object]) -> str | None:
    p = raw.get("provider")
    if isinstance(p, str) and p.strip():
        return p.strip()
    return None


def _infer_result_quality(tool_result: Any, route_source: str) -> str:
    """
    推断结果质量来源（从ToolResult透传或根据route_source判断）
    
    Returns:
        "real" - 真实工具返回
        "fallback_llm" - LLM 兜底
        "fallback_search" - 搜索兜底
        "rule" - 规则命中
        "none" - 无法判断
    """
    # 优先从ToolResult读取（源头标记）
    if hasattr(tool_result, 'result_quality'):
        quality = tool_result.result_quality
        # 如果是规则命中，覆盖为rule
        if route_source == "rule" and quality == "real":
            return "rule"
        return quality
    
    # 兜底：根据route_source判断
    if route_source == "rule":
        return "rule"
    
    return "none"


def _infer_fallback_chain(raw: dict[str, object]) -> list[str]:
    v = raw.get("fallback_chain")
    if not isinstance(v, list):
        return []
    out: list[str] = []
    for item in v:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _tool_post_system_prompt(tool_name: str) -> str:
    if tool_name == "get_stock":
        return TOOL_POST_PROMPT_STOCK
    if tool_name == "get_weather":
        return TOOL_POST_PROMPT_WEATHER
    if tool_name == "get_news":
        return TOOL_POST_PROMPT_NEWS
    if tool_name == "web_search":
        return TOOL_POST_PROMPT_SEARCH
    if tool_name == "find_nearby":
        return TOOL_POST_PROMPT_NEARBY
    return TOOL_POST_PROMPT


_WEATHER_ACTIVITY_SIGNALS = (
    "带伞", "打伞", "要伞", "下雨", "下雪", "适合", "出门", "出去",
    "穿什么", "穿多少", "穿衣", "防晒", "跑步", "骑车", "运动",
    "爬山", "开车", "出行", "户外", "遮阳", "要不要", "需要吗",
)


def _should_skip_post_llm(tool_name: str, tool_text: str, tool_raw: dict[str, object], query: str = "") -> bool:
    # If tool response is already concise and structured, skip second LLM pass for latency/stability.
    provider = str(tool_raw.get("provider") or "")
    if tool_name == "get_stock":
        if provider in {"tencent_quote", "alpha_vantage", "eastmoney"} and len(tool_text) <= 220:
            return True
    if tool_name == "get_weather":
        if provider == "qweather" and len(tool_text) <= 220:
            # Don't skip if user is asking an activity/advice question — they need a direct answer.
            if not any(k in query for k in _WEATHER_ACTIVITY_SIGNALS):
                return True
    if tool_name in {"web_search", "find_nearby", "plan_trip"}:
        if provider in {"tavily", "amap", "tavily_trip"}:
            return True
    # For news, force one LLM pass to convert URLs/snippets into readable summary.
    if tool_name == "get_news":
        return False
    return False


def _build_merged_tool_plan(
    query: str,
    tool_name: str,
    llm_tool_args: dict[str, object],
    llm_client: LLMClient,
    timeout_sec: float,
    prev_assistant_msg: str = "",
    session_ctx: dict[str, object] | None = None,
) -> ToolPlan:
    _session = session_ctx or {}

    # Use planner_v2 for find_nearby
    if tool_name == "find_nearby":
        plan_dict = build_tool_plan_v2(query=query, tool_name=tool_name, use_location_intent=True)
        missing = plan_dict.get("missing_slots", [])
        # If city is missing, use session context as fallback before asking the user.
        if "city" in missing:
            last_city = str(_session.get("last_city", "")).strip()
            if last_city:
                keyword = extract_nearby_keyword(query, city=None, default="餐厅")
                return ToolPlan(
                    tool_name=tool_name,
                    tool_args={"keyword": keyword, "city": last_city},
                    missing_slots=[],
                    extract_source="location_intent+session_city",
                )
        return ToolPlan(
            tool_name=plan_dict["tool_name"],
            tool_args=plan_dict["tool_args"],
            missing_slots=missing,
            extract_source="location_intent",
        )

    # Original logic for other tools
    # 1) fast path: rules + router llm args
    rule_args = extract_rule_tool_args(query=query, tool_name=tool_name)
    merged = dict(rule_args)
    merged.update(_sanitize_tool_args(tool_name=tool_name, tool_args=llm_tool_args))
    merged = normalize_tool_args(tool_name=tool_name, tool_args=merged, raw_query=query)
    missing = [k for k in required_slots(tool_name) if not str(merged.get(k, "")).strip()]
    if not missing:
        return ToolPlan(tool_name=tool_name, tool_args=merged, missing_slots=[], extract_source="rule_or_router")

    # 2) slow path: llm extractor fallback（带上一轮助手回复辅助实体解析）
    llm_extra = _extract_slots_with_llm(
        llm_client=llm_client,
        query=query,
        tool_name=tool_name,
        timeout_sec=timeout_sec,
        prev_assistant_msg=prev_assistant_msg,
    )
    merged.update(_sanitize_tool_args(tool_name=tool_name, tool_args=llm_extra))
    merged = normalize_tool_args(tool_name=tool_name, tool_args=merged, raw_query=query)
    missing = [k for k in required_slots(tool_name) if not str(merged.get(k, "")).strip()]

    # 3) session context fallback: use last known city for weather/trip required slots.
    if missing and _session:
        last_city = str(_session.get("last_city", "")).strip()
        if last_city:
            if tool_name == "get_weather" and "city" in missing:
                merged["city"] = last_city
                missing = [k for k in required_slots(tool_name) if not str(merged.get(k, "")).strip()]
            elif tool_name == "plan_trip" and "destination" in missing:
                merged["destination"] = last_city
                missing = [k for k in required_slots(tool_name) if not str(merged.get(k, "")).strip()]

    # 4) final fallback policy: optional-slot tools keep running with raw query.
    if tool_name in {"get_stock", "get_news", "web_search"}:
        if tool_name == "get_stock" and not str(merged.get("target", "")).strip():
            merged["target"] = query
        if tool_name == "get_news" and not str(merged.get("topic", "")).strip():
            merged["topic"] = query
        if tool_name == "web_search" and not str(merged.get("query", "")).strip():
            merged["query"] = query
        missing = [k for k in required_slots(tool_name) if not str(merged.get(k, "")).strip()]

    return ToolPlan(
        tool_name=tool_name,
        tool_args=merged,
        missing_slots=missing,
        extract_source="llm_fallback" if llm_extra else "rule_or_router",
    )


def _sanitize_tool_args(tool_name: str, tool_args: dict[str, object]) -> dict[str, object]:
    allowed: dict[str, tuple[str, ...]] = {
        "get_weather": ("city",),
        "get_news": ("topic",),
        "get_stock": ("target",),
        "find_nearby": ("keyword", "city"),
        "plan_trip": ("destination",),
        "web_search": ("query",),
    }
    ks = allowed.get(tool_name, ())
    out: dict[str, object] = {}
    for k in ks:
        v = tool_args.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            out[k] = s
    return out


def _extract_slots_with_llm(
    llm_client: LLMClient,
    query: str,
    tool_name: str,
    timeout_sec: float,
    prev_assistant_msg: str = "",
) -> dict[str, object]:
    prompt = EXTRACTOR_PROMPTS.get(tool_name)
    if not prompt:
        return {}
    try:
        # 仅在有上下文时才注入，无上下文时保持原始格式不变
        if prev_assistant_msg:
            user_input = f"参考上轮回复：{prev_assistant_msg}\n\n用户原句：{query}"
        else:
            user_input = f"用户原句：{query}"
        if hasattr(llm_client, "generate_with_timeout"):
            raw = llm_client.generate_with_timeout(  # type: ignore[attr-defined]
                user_query=user_input,
                system_prompt=prompt,
                timeout_sec=timeout_sec,
            )
        else:
            raw = llm_client.generate(user_query=user_input, system_prompt=prompt)
        obj = _extract_json_object(raw)
        if not isinstance(obj, dict):
            return {}
        args = obj.get("tool_args")
        return _extract_tool_args(args)
    except Exception:
        return {}
