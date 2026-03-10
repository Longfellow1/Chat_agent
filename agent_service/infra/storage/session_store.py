from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionRecord:
    data: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class InMemorySessionStore:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._store: dict[str, SessionRecord] = {}

    def get(self, session_id: str) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            rec = self._store.get(session_id)
            if not rec:
                return {}
            if now - rec.updated_at > self.ttl_seconds:
                self._store.pop(session_id, None)
                return {}
            return dict(rec.data)

    def upsert(self, session_id: str, patch: dict[str, Any]) -> None:
        now = time.time()
        with self._lock:
            rec = self._store.get(session_id)
            if not rec:
                self._store[session_id] = SessionRecord(data=dict(patch), updated_at=now)
                return
            rec.data.update({k: v for k, v in patch.items() if v is not None})
            rec.updated_at = now

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)
