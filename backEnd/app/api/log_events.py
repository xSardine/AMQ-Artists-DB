"""
In-memory request log, served through the authenticated /api/log/feed endpoint.
"""

from api.policy import is_private_api

import hashlib
import hmac
import secrets
import threading
import sys
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.requests import Request
from starlette.types import Scope
from settings import setting

MAX_EVENTS = 1000
_lock = threading.Lock()
_counter = 0
_stream_id = secrets.token_hex(16)
_events: deque[dict[str, Any]] = deque(maxlen=MAX_EVENTS)


def _read_env_value(key: str) -> str | None:
    return setting(key) or None


def _read_env_bool(key: str, default: bool) -> bool:
    """Parse a bool-like env value from backEnd/.env."""
    value = _read_env_value(key)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


_ANONYMIZE_IP = _read_env_bool("REQUEST_LOG_ANONYMIZE_IP", default=True)
_IP_HASH_SALT = (_read_env_value("REQUEST_LOG_IP_HASH_SALT") or "").strip()
if _ANONYMIZE_IP and not _IP_HASH_SALT:
    # Random fallback prevents plain-IP storage without forcing users to set a salt.
    # Set REQUEST_LOG_IP_HASH_SALT in backEnd/.env for stable aliases across restarts.
    _IP_HASH_SALT = secrets.token_hex(16)


def _serialize_body(body: Any) -> Any:
    """Serialize request body for JSON logging (Pydantic models omit null fields)."""
    if isinstance(body, BaseModel):
        return body.model_dump(mode="json", exclude_none=True)
    return body


def _client_ip(request: Any):
    """Use the client address resolved by the server's trusted-proxy handling."""
    if request is None:
        return None

    conn = getattr(request, "client", None)
    if conn is not None:
        host = getattr(conn, "host", None)
        if host:
            return str(host)

    return None


def _ip_alias(ip: str | None) -> str | None:
    """Return a deterministic, non-reversible alias for an IP address."""
    if not ip:
        return None
    if not _ANONYMIZE_IP:
        return ip

    digest = hmac.new(
        _IP_HASH_SALT.encode("utf-8"),
        ip.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:6].upper()


def _client_id(request: Any) -> str | None:
    """Caller label from X-Client-Id (e.g. AnisongDB)."""
    if request is None:
        return None
    return request.headers.get("x-client-id") or None


def _request_context(request: Any) -> dict[str, Any]:
    """Build per-event metadata from the Starlette request (IP, optional X-Client-Id)."""
    context: dict[str, Any] = {"ip": _ip_alias(_client_ip(request))}
    client_identifier = _client_id(request)
    if client_identifier is not None:
        context["client"] = client_identifier
    return context


def _request_summary(body_data: Any) -> str:
    """One-line console summary: search text or IDs only."""
    if not isinstance(body_data, dict):
        return ""

    search_bits: list[tuple[str, str]] = []
    for key, label in (
        ("anime_search_filter", "anime"),
        ("song_name_search_filter", "song"),
        ("artist_search_filter", "artist"),
        ("composer_search_filter", "composer"),
    ):
        filt = body_data.get(key)
        if isinstance(filt, dict):
            search = filt.get("search")
            if isinstance(search, str) and search:
                search_bits.append((label, search))
    if search_bits:
        searches = [search for _, search in search_bits]
        if len(searches) == 4 and len(set(searches)) == 1:
            return f"main={searches[0]}"
        return " ".join(f"{label}={search}" for label, search in search_bits)

    for id_key in (
        "artist_ids",
        "composer_ids",
        "ann_ids",
        "mal_ids",
        "anilist_ids",
        "kitsu_ids",
        "anidb_ids",
        "ann_song_ids",
        "amq_song_ids",
    ):
        ids = body_data.get(id_key)
        if ids:
            return f"{id_key}={ids}"

    if body_data.get("annId") is not None:
        return f"annId={body_data['annId']}"

    if body_data.get("season"):
        return f"season={body_data['season']}"

    if body_data.get("n") is not None:
        return f"n={body_data['n']}"

    return ""


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
    """Stage request metadata; HTTP middleware records the final status and duration."""
    body_data = _serialize_body(body)
    payload: dict[str, Any] = {
        "endpoint": endpoint,
        "http_status": http_status,
        "body": body_data,
        **_request_context(request),
    }

    if http_status >= 400:
        if reason is not None:
            payload["reason"] = reason
        if errors is not None:
            payload["errors"] = errors
    elif result_count is not None:
        payload["result"] = {"count": result_count}

    if duration_ms is not None:
        payload["duration_ms"] = duration_ms

    state = request.scope.get("state", {}) if request is not None else {}
    if state.get("_request_log_deferred"):
        state["_request_log_event"] = payload
    else:
        _append_event(payload)

    if http_status >= 400 and raise_http_exception:
        raise HTTPException(status_code=http_status, detail=detail or reason or "Request failed")


def finish_request(scope: Scope, http_status: int, duration_ms: int) -> None:
    """Commit at response start (or unhandled failure), without logging feed polling."""
    if is_private_api(scope["path"]):
        return
    state = scope.setdefault("state", {})
    payload = state.pop("_request_log_event", None)
    if payload is None:
        if http_status < 400:
            return
        payload = {
            "endpoint": scope["path"],
            "body": None,
            **_request_context(Request(scope)),
        }

    previous_status = payload.get("http_status")
    payload["http_status"] = http_status
    payload["duration_ms"] = duration_ms
    if http_status >= 400:
        payload.pop("result", None)
        if previous_status != http_status:
            payload.pop("errors", None)
            payload["reason"] = "Internal server error" if http_status >= 500 else "Request failed"

    _append_event(payload)


def _append_event(payload: dict[str, Any]) -> None:
    # Pydantic error contexts can contain ValueError objects. Store a JSON-safe
    # snapshot once so a rejected request cannot break subsequent feed polls.
    payload = jsonable_encoder(payload, custom_encoder={Exception: str})
    summary = _request_summary(payload["body"])
    if summary:
        if "duration_ms" in payload:
            summary += f" ({payload['duration_ms']}ms)"
        try:
            print("LOG: " + summary, flush=True)
        except UnicodeEncodeError:
            # Windows consoles may use a legacy encoding; logging must not fail a search.
            encoding = sys.stdout.encoding or "utf-8"
            safe_summary = summary.encode(encoding, errors="backslashreplace").decode(encoding)
            print("LOG: " + safe_summary, flush=True)

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

    return {"events": items, "latest_id": latest_id, "stream_id": _stream_id}
