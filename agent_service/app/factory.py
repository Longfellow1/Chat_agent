from __future__ import annotations

import os

from app.orchestrator.chat_flow import ChatFlow
from domain.tools.executor import ToolExecutor
from infra.llm_clients.coze_client import CozeClient
from infra.llm_clients.lm_studio_client import LMStudioClient
from infra.storage.session_store import InMemorySessionStore


def build_flow() -> ChatFlow:
    tool_executor = ToolExecutor()
    session_store = InMemorySessionStore(ttl_seconds=int(os.getenv("SESSION_TTL_SEC", "1800")))
    backend = os.getenv("AGENT_BACKEND", "lmstudio").strip().lower()
    if backend == "coze":
        return ChatFlow(llm_client=CozeClient(), tool_executor=tool_executor, session_store=session_store)
    return ChatFlow(llm_client=LMStudioClient(), tool_executor=tool_executor, session_store=session_store)
