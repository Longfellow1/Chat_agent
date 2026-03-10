from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(self, user_query: str, system_prompt: str) -> str:
        ...
