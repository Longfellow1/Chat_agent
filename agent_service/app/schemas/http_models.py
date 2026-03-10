from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequestBody(BaseModel):
    query: str = Field(min_length=1)
    session_id: str | None = None
    user_id: str | None = None


class ApiEnvelope(BaseModel):
    code: str
    message: str
    trace_id: str
    data: dict
