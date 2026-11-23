"""Request log feed response contracts."""

from typing import Any
from pydantic import BaseModel


class LogResult(BaseModel):
    count: int


class LogEvent(BaseModel):
    id: str
    ts: str
    endpoint: str
    http_status: int
    body: Any
    ip: str | None = None
    client: str | None = None
    reason: str | None = None
    errors: Any = None
    duration_ms: int | None = None
    result: LogResult | None = None


class LogFeed(BaseModel):
    events: list[LogEvent]
    latest_id: str | None
    stream_id: str
