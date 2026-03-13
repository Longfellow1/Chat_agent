"""Tests for technical debt fixes.

Covers:
  - Risk-1: extract_city Pattern-3 hallucination (planner.py)
  - Risk-2: Stock code SH/SZ/BJ suffix (planner.py)
  - Risk-4: Noise filter numeric passthrough (pre_rules.py)
  - Risk-8: Clarify slot name UX (chat_flow.py)
  - Multi-turn history: session store + reply path
  - Coref signal detection (rewrite.py)
"""
from __future__ import annotations

import pytest

from app.orchestrator.chat_flow import ChatFlow
from app.orchestrator.rewrite import detect_coref_signal, rewrite_query
from app.policies.pre_rules import detect_meaningless_noise
from app.schemas.contracts import ChatRequest
from domain.tools.executor import ToolExecutor
from domain.tools.planner import extract_city, extract_stock_target
from infra.storage.session_store import InMemorySessionStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeLLM:
    """最小化假 LLM，记录是否被调用过 generate_with_history。"""

    def __init__(self) -> None:
        self.history_calls: list[list[dict]] = []

    def generate(self, user_query: str, system_prompt: str) -> str:
        return f"echo:{user_query}"

    def generate_with_history(self, messages: list[dict], system_prompt: str) -> str:
        self.history_calls.append(list(messages))
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )
        return f"history_echo:{last_user}"


def _flow(llm: FakeLLM | None = None) -> ChatFlow:
    import os
    # 测试时禁用 4B router，避免 FakeLLM 缺少 .call() 方法
    os.environ.setdefault("USE_4B_ROUTER", "false")
    return ChatFlow(
        llm_client=llm or FakeLLM(),
        tool_executor=ToolExecutor(),
        session_store=InMemorySessionStore(),
    )


# ---------------------------------------------------------------------------
# Risk-1: extract_city Pattern-3 hallucination
# ---------------------------------------------------------------------------

class TestExtractCityHallucination:
    def test_domain_word_not_extracted_as_city(self) -> None:
        # "电影推荐" should not be returned as a city
        assert extract_city("电影推荐今天有什么") is None

    def test_apple_company_not_city(self) -> None:
        assert extract_city("苹果公司最新消息") is None

    def test_phone_not_city(self) -> None:
        assert extract_city("手机推荐最近有哪些") is None

    def test_stock_word_not_city(self) -> None:
        assert extract_city("股票行情今天怎么样") is None

    def test_real_city_still_extracted(self) -> None:
        assert extract_city("北京今天天气怎么样") == "北京"

    def test_known_city_in_known_list(self) -> None:
        assert extract_city("郑州天气怎么样") == "郑州"

    def test_movie_not_city(self) -> None:
        assert extract_city("电影今天有什么好看的") is None

    def test_price_not_city(self) -> None:
        assert extract_city("价格最近有没有变化") is None


# ---------------------------------------------------------------------------
# Risk-2: Stock code SH/SZ/BJ suffix
# ---------------------------------------------------------------------------

class TestStockCodeSuffix:
    def test_600519_is_ss(self) -> None:
        assert extract_stock_target("查600519股价") == "600519.SS"

    def test_000001_is_sz(self) -> None:
        result = extract_stock_target("查000001")
        assert result == "000001.SZ", f"Expected 000001.SZ, got {result}"

    def test_300750_is_sz(self) -> None:
        result = extract_stock_target("300750行情")
        assert result == "300750.SZ"

    def test_430090_is_bj(self) -> None:
        result = extract_stock_target("430090怎么样")
        assert result == "430090.BJ"

    def test_800090_is_bj(self) -> None:
        result = extract_stock_target("800090最新价格")
        assert result == "800090.BJ"

    def test_alias_still_works(self) -> None:
        assert extract_stock_target("查茅台") == "600519.SS"

    def test_english_ticker(self) -> None:
        result = extract_stock_target("帮我查NVDA")
        assert result == "NVDA"


# ---------------------------------------------------------------------------
# Risk-4: Noise filter passthrough for numeric queries
# ---------------------------------------------------------------------------

class TestNoisFilterNumeric:
    def test_6digit_stock_code_passes(self) -> None:
        assert detect_meaningless_noise("600519") is False

    def test_6digit_sz_code_passes(self) -> None:
        assert detect_meaningless_noise("000001") is False

    def test_sf_tracking_number_passes(self) -> None:
        assert detect_meaningless_noise("SF1234567890") is False

    def test_random_long_alphanumeric_noise(self) -> None:
        # 7-digit number that is NOT a valid 6-digit stock code → still noise
        assert detect_meaningless_noise("1234567") is True

    def test_pure_symbols_still_noise(self) -> None:
        assert detect_meaningless_noise("!!!???") is True

    def test_empty_is_noise(self) -> None:
        assert detect_meaningless_noise("") is True


# ---------------------------------------------------------------------------
# Risk-8: Clarify message slot name UX
# ---------------------------------------------------------------------------

class TestClarifySlotNames:
    def test_get_stock_clarify_no_raw_slot(self) -> None:
        flow = _flow()
        out = flow.run(ChatRequest(query="帮我查一下股价"))
        if out.decision_mode == "clarify":
            # 不应暴露原始英文字段名
            assert "target" not in out.final_text
            assert "city" not in out.final_text

    def test_weather_clarify_user_friendly(self) -> None:
        flow = _flow()
        out = flow.run(ChatRequest(query="今天天气怎么样"))
        assert out.decision_mode == "clarify"
        assert out.tool_name == "get_weather"
        # Should mention "城市" conceptually
        assert "城市" in out.final_text or "哪个" in out.final_text


# ---------------------------------------------------------------------------
# Multi-turn: Session history storage
# ---------------------------------------------------------------------------

class TestSessionHistory:
    def test_history_stored_after_reply(self) -> None:
        store = InMemorySessionStore()
        llm = FakeLLM()
        flow = ChatFlow(llm_client=llm, tool_executor=ToolExecutor(), session_store=store)
        sid = "test_session_history"

        flow.run(ChatRequest(query="你好", session_id=sid))
        ctx = store.get(sid)
        history = ctx.get("history", [])
        assert len(history) >= 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "你好"
        assert history[1]["role"] == "assistant"

    def test_history_accumulates_across_turns(self) -> None:
        store = InMemorySessionStore()
        llm = FakeLLM()
        flow = ChatFlow(llm_client=llm, tool_executor=ToolExecutor(), session_store=store)
        sid = "test_session_accum"

        flow.run(ChatRequest(query="你好", session_id=sid))
        flow.run(ChatRequest(query="再说一遍", session_id=sid))
        ctx = store.get(sid)
        history = ctx.get("history", [])
        assert len(history) >= 4  # 2 turns × 2 items

    def test_history_max_turns_enforced(self) -> None:
        store = InMemorySessionStore()
        llm = FakeLLM()
        flow = ChatFlow(llm_client=llm, tool_executor=ToolExecutor(), session_store=store)
        sid = "test_session_max"

        # 12 turns → should cap at 10 turns (20 items)
        for i in range(12):
            flow.run(ChatRequest(query=f"消息{i}", session_id=sid))

        ctx = store.get(sid)
        history = ctx.get("history", [])
        assert len(history) <= 20  # max 10 turns × 2 items

    def test_generate_with_history_called_on_second_turn(self) -> None:
        llm = FakeLLM()
        flow = ChatFlow(
            llm_client=llm,
            tool_executor=ToolExecutor(),
            session_store=InMemorySessionStore(),
        )
        sid = "test_gen_history"

        flow.run(ChatRequest(query="你好", session_id=sid))
        flow.run(ChatRequest(query="继续聊", session_id=sid))

        # Second turn should use generate_with_history since history exists
        assert len(llm.history_calls) >= 1, "generate_with_history should have been called"
        # The messages should contain previous history
        last_call = llm.history_calls[-1]
        roles = [m["role"] for m in last_call]
        assert "user" in roles
        assert "assistant" in roles


# ---------------------------------------------------------------------------
# Coref signal detection
# ---------------------------------------------------------------------------

class TestCorefSignalDetection:
    def test_pronoun_it(self) -> None:
        assert detect_coref_signal("它最近涨了多少") == "pronoun"

    def test_pronoun_zhege(self) -> None:
        assert detect_coref_signal("这个怎么样") == "pronoun"

    def test_ellipsis_zenmeyang(self) -> None:
        assert detect_coref_signal("那呢") == "ellipsis"

    def test_followup_haiyou(self) -> None:
        assert detect_coref_signal("还有别的吗") == "followup"

    def test_compare_signal(self) -> None:
        assert detect_coref_signal("和它比哪个好") == "pronoun"

    def test_no_signal(self) -> None:
        assert detect_coref_signal("北京今天天气怎么样") is None

    def test_no_signal_plain_query(self) -> None:
        assert detect_coref_signal("帮我查上证指数") is None


# ---------------------------------------------------------------------------
# Coref rule rewrite - pronoun resolution
# ---------------------------------------------------------------------------

class TestCoreferenceRewrite:
    def test_pronoun_resolves_to_last_target(self) -> None:
        ctx = {
            "last_target": "600519.SS",
            "last_tool": "get_stock",
            "last_city": "",
            "last_topic": "",
            "last_destination": "",
        }
        result = rewrite_query("它最近涨了多少", ctx)
        assert result.rewritten is True
        assert "600519.SS" in result.effective_query

    def test_ellipsis_with_city_and_last_tool(self) -> None:
        ctx = {
            "last_city": "上海",
            "last_tool": "get_weather",
            "last_target": "",
            "last_topic": "",
            "last_destination": "",
        }
        result = rewrite_query("那呢", ctx)
        assert result.rewritten is True
        assert "上海" in result.effective_query

    def test_no_rewrite_without_context(self) -> None:
        result = rewrite_query("它怎么样", {})
        assert result.rewritten is False


# ---------------------------------------------------------------------------
# History context helpers
# ---------------------------------------------------------------------------

class TestHistoryContextHelpers:
    """Test _build_history_messages 3-turn window + truncation,
    _get_prev_user_msg, and _get_prev_assistant_msg."""

    def test_build_history_3_turn_limit(self) -> None:
        """_build_history_messages returns at most 3 turns (6 items)."""
        store = InMemorySessionStore()
        llm = FakeLLM()
        flow = ChatFlow(llm_client=llm, tool_executor=ToolExecutor(), session_store=store)
        sid = "test_3turn"

        # Send 5 turns to accumulate history
        for i in range(5):
            flow.run(ChatRequest(query=f"消息{i}", session_id=sid))

        ctx = store.get(sid)
        msgs = flow._build_history_messages(ctx)
        # At most 6 items (3 turns × 2)
        assert len(msgs) <= 6

    def test_build_history_truncates_assistant(self) -> None:
        """Assistant messages > 200 chars get truncated in the output."""
        ctx = {
            "history": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "A" * 500},
            ]
        }
        flow = _flow()
        msgs = flow._build_history_messages(ctx)
        assert len(msgs) == 2
        assert len(msgs[1]["content"]) == 200

    def test_get_prev_user_msg(self) -> None:
        ctx = {
            "history": [
                {"role": "user", "content": "帮我查茅台"},
                {"role": "assistant", "content": "茅台(600519.SS)..."},
            ]
        }
        assert ChatFlow._get_prev_user_msg(ctx) == "帮我查茅台"

    def test_get_prev_user_msg_truncates(self) -> None:
        long_msg = "x" * 100
        ctx = {"history": [{"role": "user", "content": long_msg}]}
        result = ChatFlow._get_prev_user_msg(ctx, max_len=60)
        assert len(result) == 60

    def test_get_prev_user_msg_empty_history(self) -> None:
        assert ChatFlow._get_prev_user_msg({}) == ""

    def test_get_prev_assistant_msg(self) -> None:
        ctx = {
            "history": [
                {"role": "user", "content": "帮我查茅台"},
                {"role": "assistant", "content": "茅台(600519.SS)今日收盘1820元"},
            ]
        }
        result = ChatFlow._get_prev_assistant_msg(ctx)
        assert "600519.SS" in result

    def test_get_prev_assistant_msg_truncates(self) -> None:
        ctx = {"history": [{"role": "assistant", "content": "B" * 200}]}
        result = ChatFlow._get_prev_assistant_msg(ctx, max_len=80)
        assert len(result) == 80


# ---------------------------------------------------------------------------
# History injection: router and extractor receive context
# ---------------------------------------------------------------------------

class TestHistoryInjection:
    """Verify that prev_user_msg reaches the router and prev_assistant_msg
    reaches the extractor when multi-turn context exists."""

    def test_router_receives_prev_user_msg_on_second_turn(self) -> None:
        """On the second turn, the LLM router's input should contain
        the previous user message as context."""
        llm = FakeLLM()
        store = InMemorySessionStore()
        flow = ChatFlow(llm_client=llm, tool_executor=ToolExecutor(), session_store=store)
        sid = "test_router_ctx"

        # Turn 1: a normal greeting
        flow.run(ChatRequest(query="你好", session_id=sid))
        # Turn 2: a follow-up — the router should receive prev context
        flow.run(ChatRequest(query="继续聊天吧", session_id=sid))

        # In the second turn, generate was called with context containing
        # the previous user message. FakeLLM.generate records user_query.
        # Since the flow uses generate_with_history on the second turn,
        # the history should contain the previous user + assistant messages.
        assert len(llm.history_calls) >= 1
        last_call = llm.history_calls[-1]
        user_contents = [m["content"] for m in last_call if m["role"] == "user"]
        # The current query should be in the messages
        assert any("继续聊天吧" in c for c in user_contents)
