"""Independent shared-password sessions, deliberately lost on process restart."""

import hashlib
import hmac
import secrets
import threading
import time
from collections import OrderedDict

from fastapi import HTTPException, Request, Response

from settings import frontend_origins, setting

_lock = threading.Lock()
_sessions: dict[tuple[str, str], str] = {}
_attempts: OrderedDict[tuple[str, str], list[float]] = OrderedDict()


def reset_sessions() -> None:
    with _lock:
        _sessions.clear()
        _attempts.clear()


def rate_limit(request: Request, purpose: str, maximum: int, seconds: int) -> None:
    """Use the client address resolved by the server's trusted-proxy handling."""
    key = (purpose, request.client.host if request.client else "unknown")
    now = time.monotonic()
    with _lock:
        history = [stamp for stamp in _attempts.pop(key, []) if now - stamp < seconds]
        if len(history) >= maximum:
            _attempts[key] = history
            raise HTTPException(429, "Too many attempts. Please try again later.")
        history.append(now)
        _attempts[key] = history
        while len(_attempts) > 4096:
            _attempts.popitem(last=False)


def require_origin(request: Request) -> None:
    if request.headers.get("origin", "").rstrip("/") not in frontend_origins():
        raise HTTPException(403, "Request origin is not allowed.")


def require_session(request: Request, purpose: str) -> str:
    token = request.cookies.get(f"anisongdb_{purpose}", "")
    with _lock:
        name = _sessions.get((purpose, hashlib.sha256(token.encode()).hexdigest()))
    if name is None:
        raise HTTPException(401, "Please sign in again.")
    return name


def verify_password(password: str, stored: str) -> None:
    if not stored:
        raise HTTPException(503, "Access has not been configured.")
    if not hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8")):
        raise HTTPException(401, "Incorrect password.")


def create_session(request: Request, response: Response, purpose: str, name: str) -> dict:
    token = secrets.token_urlsafe(32)
    with _lock:
        old = request.cookies.get(f"anisongdb_{purpose}")
        if old:
            _sessions.pop((purpose, hashlib.sha256(old.encode()).hexdigest()), None)
        _sessions[(purpose, hashlib.sha256(token.encode()).hexdigest())] = name
    secure = setting("AUTH_COOKIE_SECURE", "").lower()
    secure_cookie = (
        secure == "true"
        if secure
        else request.url.hostname not in {"localhost", "127.0.0.1", "testserver"}
    )
    response.set_cookie(
        f"anisongdb_{purpose}",
        token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/api",
        max_age=31536000,
    )
    response.headers["Cache-Control"] = "no-store"
    return {"authenticated": True, "name": name}


def session(request: Request, response: Response, purpose: str) -> dict:
    response.headers["Cache-Control"] = "no-store"
    try:
        name = require_session(request, purpose)
        return {"authenticated": True, "name": name}
    except HTTPException:
        return {"authenticated": False, "name": ""}


def logout(request: Request, response: Response, purpose: str) -> dict:
    require_origin(request)
    token = request.cookies.get(f"anisongdb_{purpose}", "")
    with _lock:
        _sessions.pop((purpose, hashlib.sha256(token.encode()).hexdigest()), None)
    response.delete_cookie(f"anisongdb_{purpose}", path="/api")
    response.headers["Cache-Control"] = "no-store"
    return {"authenticated": False}
