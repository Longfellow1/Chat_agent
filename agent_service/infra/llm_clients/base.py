from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(self, user_query: str, system_prompt: str) -> str:
        ...

    def generate_with_history(self, messages: list[dict], system_prompt: str) -> str:
        ...
