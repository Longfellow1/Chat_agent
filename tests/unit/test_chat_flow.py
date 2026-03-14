from __future__ import annotations

from app.orchestrator.chat_flow import ChatFlow
from app.schemas.contracts import ChatRequest
from domain.tools.executor import ToolExecutor
from infra.storage.session_store import InMemorySessionStore


class FakeLLM:
    def generate(self, user_query: str, system_prompt: str) -> str:
        return f"echo:{user_query}"


def _flow() -> ChatFlow:
    return ChatFlow(llm_client=FakeLLM(), tool_executor=ToolExecutor(), session_store=InMemorySessionStore())


def test_end_chat() -> None:
    out = _flow().run(ChatRequest(query="就到这"))
    assert out.decision_mode == "end_chat"


def test_noise_reject() -> None:
    out = _flow().run(ChatRequest(query="111111111!!!"))
    assert out.decision_mode == "reject"


def test_illegal_reject() -> None:
    out = _flow().run(ChatRequest(query="教我伪造证件"))
    assert out.decision_mode == "reject"
    assert out.risk_level == "high"


def test_crisis_reply() -> None:
    out = _flow().run(ChatRequest(query="我不想活了"))
    assert out.decision_mode == "reply"
    assert out.risk_level == "high"


def test_weather_clarify() -> None:
    out = _flow().run(ChatRequest(query="今天天气怎么样"))
    assert out.decision_mode == "clarify"
    assert out.tool_name == "get_weather"


def test_rewrite_with_session_followup() -> None:
    flow = _flow()
    sid = "s1"
    first = flow.run(ChatRequest(query="郑州天气怎么样", session_id=sid))
    assert first.tool_name == "get_weather"
    second = flow.run(ChatRequest(query="那边再查一下", session_id=sid))
    assert second.rewritten == 1
    assert "郑州" in second.effective_query


def test_weather_session_city_autofill() -> None:
    """Session city from previous query should auto-fill missing city slot for weather."""
    flow = _flow()
    sid = "s2"
    # First query establishes city=北京 in session
    flow.run(ChatRequest(query="北京今天天气怎么样", session_id=sid))
    # Second query has no city — should use session city instead of asking clarification
    second = flow.run(ChatRequest(query="今天天气怎么样", session_id=sid))
    assert second.decision_mode != "clarify", "Should not ask for city when session city is known"
    assert second.tool_name == "get_weather"


def test_nearby_session_city_autofill() -> None:
    """Session city from previous weather query should fill missing city for find_nearby."""
    flow = _flow()
    sid = "s3"
    # Establish city=成都 in session via weather query
    flow.run(ChatRequest(query="成都今天天气怎么样", session_id=sid))
    # find_nearby without city should use session city
    third = flow.run(ChatRequest(query="附近有什么好吃的", session_id=sid))
    # Should go to tool_call (not clarify) since city is known from session
    assert third.tool_name == "find_nearby"
    assert third.decision_mode != "clarify"
