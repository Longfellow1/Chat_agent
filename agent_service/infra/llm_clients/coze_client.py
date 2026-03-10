from __future__ import annotations

import json
import os
import urllib.request


class CozeClient:
    """Minimal Coze Bot Chat client.

    Note: this client requires a PAT with bot chat permission.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("COZE_API_BASE", "https://api.coze.cn")
        self.bot_id = os.getenv("COZE_BOT_ID", "")
        self.token = os.getenv("COZE_API_TOKEN", "")
        self.timeout = float(os.getenv("COZE_TIMEOUT_SEC", "60"))

    def generate(self, user_query: str, system_prompt: str) -> str:
        if not self.bot_id or not self.token:
            raise RuntimeError("missing COZE_BOT_ID or COZE_API_TOKEN")

        payload = {
            "bot_id": self.bot_id,
            "user_id": "local-dev",
            "stream": False,
            "additional_messages": [
                {"role": "system", "content": system_prompt, "content_type": "text"},
                {"role": "user", "content": user_query, "content_type": "text"},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/v3/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        if body.get("code") not in (0, "0"):
            raise RuntimeError(f"coze error: code={body.get('code')} msg={body.get('msg')}")

        data = body.get("data", {})
        if isinstance(data, dict):
            answer = data.get("content") or data.get("answer")
            if answer:
                return str(answer).strip()
        return ""
