"""
In-memory request log (JSON). Viewer URL segment from backEnd/.env (REQUEST_LOG_URL_SEGMENT).
"""

import threading
from pathlib import Path
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel

MAX_EVENTS = 1000
_DEFAULT_URL_SEGMENT = "log"
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_lock = threading.Lock()
_counter = 0
_events: deque[dict[str, Any]] = deque(maxlen=MAX_EVENTS)


def _read_env_value(key: str) -> str | None:
    """Read a single KEY=value from backEnd/.env (no os.environ)."""
    if not _ENV_PATH.is_file():
        return None
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() == key:
            return value.strip().strip('"').strip("'")
    return None


def get_request_log_path() -> str:
    """URL path segment for the HTML viewer (default: log)."""
    segment = (_read_env_value("REQUEST_LOG_URL_SEGMENT") or "").strip().strip("/")
    return segment or _DEFAULT_URL_SEGMENT


def _serialize_body(body: Any) -> Any:
    """Serialize request body for JSON logging (Pydantic models omit null fields)."""
    if isinstance(body, BaseModel):
        return body.model_dump(mode="json", exclude_none=True)
    return body


def _client_ip(request: Any):
    """Best-effort client IP (X-Forwarded-For first hop, else direct connection)."""
    if request is None:
        return None

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None

    conn = getattr(request, "client", None)
    if conn is not None:
        host = getattr(conn, "host", None)
        if host:
            return str(host)

    return None


def _client_id(request: Any) -> str | None:
    """Caller label from X-Client-Id (e.g. AnisongDB)."""
    if request is None:
        return None
    return request.headers.get("x-client-id") or None


def _request_context(request: Any) -> dict[str, Any]:
    """Build per-event metadata from the Starlette request (IP, optional X-Client-Id)."""
    context: dict[str, Any] = {"ip": _client_ip(request)}
    client_identifier = _client_id(request)
    if client_identifier is not None:
        context["client"] = client_identifier
    return context


def record_request(
    endpoint: str,
    body: Any,
    request: Any = None,
    *,
    http_status: int = 200,
    reason: str | None = None,
    detail: str | None = None,
    result_count: int | None = None,
    duration_ms: int | None = None,
    errors: Any = None,
    raise_http_exception: bool = True,
) -> None:
    """Log a request event and append it to the ring buffer.

    Outcome is derived from http_status (2xx vs 4xx/5xx). On http_status >= 400, logs
    reason (and optional errors) then raises HTTPException when raise_http_exception is
    True (default). Success events include result.count and result.duration_ms when
    provided.
    """
    payload: dict[str, Any] = {
        "endpoint": endpoint,
        "http_status": http_status,
        "body": _serialize_body(body),
        **_request_context(request),
    }

    if http_status >= 400:
        if reason is not None:
            payload["reason"] = reason
        if errors is not None:
            payload["errors"] = errors
    elif result_count is not None or duration_ms is not None:
        payload["result"] = {
            "count": result_count if result_count is not None else 0,
            "duration_ms": duration_ms if duration_ms is not None else 0,
        }

    with _lock:
        global _counter
        _counter += 1
        _events.append(
            {
                "id": str(_counter),
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                **payload,
            }
        )

    if http_status >= 400 and raise_http_exception:
        raise HTTPException(status_code=http_status, detail=detail or reason or "Request failed")


def get_feed_payload(since: str | None = None, limit: int = 100):
    """Returns JSON feed shape for the log viewer: events list plus latest_id cursor."""
    max_limit = min(max(1, limit), MAX_EVENTS)

    with _lock:
        items = list(_events)
    if since is not None:
        try:
            since_id = int(since)
        except ValueError:
            since_id = -1
        items = [e for e in items if int(e["id"]) > since_id]

    if len(items) > max_limit:
        items = items[-max_limit:]
    latest_id = items[-1]["id"] if items else since

    return {"events": items, "latest_id": latest_id}
