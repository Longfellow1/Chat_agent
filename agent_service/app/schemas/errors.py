from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorDef:
    code: str
    message: str
    http_status: int


INVALID_REQUEST = ErrorDef("A0001", "invalid request", 400)
BAD_JSON = ErrorDef("A0002", "invalid json body", 400)
INTERNAL_ERROR = ErrorDef("A0003", "internal server error", 500)
BACKEND_UNAVAILABLE = ErrorDef("A0004", "llm backend unavailable", 502)
