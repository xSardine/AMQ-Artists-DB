"""Record HTTP response preparation time, final statuses, and validation/error details."""

from api.policy import is_private_api

from time import perf_counter
from typing import NoReturn

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api import log_events
from api.schemas import SongSelectionRequest


class RequestTimingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = perf_counter()
        scope.setdefault("state", {})["_request_log_deferred"] = True
        response_started = False

        async def timed_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                log_events.finish_request(
                    scope, message["status"], int((perf_counter() - start) * 1000)
                )
            await send(message)

        try:
            await self.app(scope, receive, timed_send)
        except Exception:
            # Starlette's outer error middleware produces the generic 500 response.
            # Record time-to-failure here; never leave a staged success in the log.
            if not response_started:
                log_events.finish_request(scope, 500, int((perf_counter() - start) * 1000))
            raise


async def logged_http_exception_handler(request: Request, exc: HTTPException):
    if "_request_log_event" not in request.scope.get("state", {}):
        log_events.record_request(
            request.url.path,
            None,
            request,
            http_status=exc.status_code,
            reason=str(exc.detail),
            raise_http_exception=False,
        )
    return await http_exception_handler(request, exc)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if is_private_api(request.url.path):
        return await request_validation_exception_handler(request, exc)
    body = exc.body
    if isinstance(body, (bytes, bytearray)):
        try:
            body = body.decode()
        except UnicodeDecodeError:
            body = repr(body)

    log_events.record_request(
        request.url.path,
        body,
        request,
        http_status=422,
        reason="Validation error",
        errors=exc.errors(),
        raise_http_exception=False,
    )
    return await request_validation_exception_handler(request, exc)


def reject_request(
    request: Request,
    query: SongSelectionRequest,
    *,
    status_code: int,
    reason: str,
    detail: str,
) -> NoReturn:
    """Stage a query-specific rejection before the shared exception handler responds."""
    log_events.record_request(
        request.url.path,
        query,
        request,
        http_status=status_code,
        reason=reason,
        detail=detail,
        raise_http_exception=False,
    )
    raise HTTPException(status_code=status_code, detail=detail)


def install_request_logging(app: FastAPI) -> None:
    """Install after gzip and CORS so recorded preparation time includes those layers."""
    app.add_middleware(RequestTimingMiddleware)
    app.add_exception_handler(HTTPException, logged_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
