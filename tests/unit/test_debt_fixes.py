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
