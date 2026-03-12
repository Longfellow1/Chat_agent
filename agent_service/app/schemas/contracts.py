from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ChatRequest:
    query: str
    session_id: str | None = None
    user_id: str | None = None


@dataclass
class LatencyMs:
    router: int = 0
    llm: int = 0
    tools: int = 0
    total: int = 0


@dataclass
class ChatResponse:
    query: str
    effective_query: str
    rewritten: int = 0
    rewrite_source: str = "none"
    route_source: str = "unknown"
    intent_probs: dict[str, float] = field(default_factory=dict)
    decision_mode: str = "reply"
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    extract_source: str = "none"
    tool_status: str = "none"
    tool_provider: str | None = None
    tool_error: str | None = None
    fallback_chain: list[str] = field(default_factory=list)
    result_quality: str = "none"  # "real" | "fallback_llm" | "fallback_search" | "rule" | "none"
    post_llm_applied: bool = False
    post_llm_timeout: bool = False
    missing_slots: list[str] = field(default_factory=list)
    risk_level: str = "none"
    final_text: str = ""
    latency_ms: LatencyMs = field(default_factory=LatencyMs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
