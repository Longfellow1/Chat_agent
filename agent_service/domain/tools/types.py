from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    ok: bool
    text: str
    raw: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
