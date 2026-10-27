"""Log access and the protected in-memory request feed."""

from fastapi import APIRouter, Depends, Query, Request, Response

from api import log_events
from api.access import create_session, logout, rate_limit, require_origin, session, verify_password
from api.access_schemas import AccessSession, LogLogin, LogoutResult
from api.dependencies import require_log_access
from api.log_schemas import LogFeed
from settings import setting

router = APIRouter(prefix="/api/log", include_in_schema=False)
protected = APIRouter(dependencies=[Depends(require_log_access)])


@router.post("/login", response_model=AccessSession)
def login(request: Request, response: Response, data: LogLogin):
    require_origin(request)
    rate_limit(request, "log-login", 5, 300)
    verify_password(data.password, setting("LOG_PASSWORD"))
    return create_session(request, response, "log", "")


@router.get("/session", response_model=AccessSession)
def current_session(request: Request, response: Response):
    return session(request, response, "log")


@router.post("/logout", response_model=LogoutResult)
def end_session(request: Request, response: Response):
    return logout(request, response, "log")


@protected.get("/feed", response_model=LogFeed, response_model_exclude_unset=True)
def feed(
    since: str | None = Query(default=None, max_length=30, pattern=r"^[0-9]+$"),
    limit: int = Query(default=100, ge=1, le=log_events.MAX_EVENTS),
):
    return log_events.get_feed_payload(since, limit)


router.include_router(protected)
