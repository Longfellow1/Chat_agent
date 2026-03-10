from __future__ import annotations

import json
import os
import urllib.request


class LMStudioClient:
    """LM Studio client for local LLM inference.
    
    Model Selection:
    - Default: qwen2.5-7b-instruct-mlx
    - Reason: qwen3.5-9b-mlx outputs "Thinking Process:" that cannot be disabled via prompt
    - Alternative: Any instruct model without thinking mode
    
    If you need to change models, ensure the new model does NOT output thinking process,
    as it will appear in user-facing content and degrade output quality.
    """
    def __init__(self) -> None:
        self.base_url = os.getenv("LM_STUDIO_BASE", "http://localhost:1234")
        # Use 7B instruct - no thinking mode (qwen3.5-9b-mlx has uncontrollable thinking output)
        self.model = os.getenv("LM_STUDIO_MODEL", "qwen2.5-7b-instruct-mlx")
        self.timeout = float(os.getenv("LM_STUDIO_TIMEOUT_SEC", "60"))

    def generate(self, user_query: str, system_prompt: str) -> str:
        return self.generate_with_timeout(user_query=user_query, system_prompt=system_prompt, timeout_sec=self.timeout)

    def generate_with_timeout(self, user_query: str, system_prompt: str, timeout_sec: float) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            "temperature": 0.2,
            "max_tokens": 512,
            "stream": False,
            "thinking": {
                "type": "disabled"
            }
        }
        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
