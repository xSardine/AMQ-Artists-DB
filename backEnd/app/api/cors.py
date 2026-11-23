"""HTTP origin and cache policy for public and private endpoints."""

from starlette.middleware.cors import CORSMiddleware
from settings import frontend_origins
from api.policy import is_private_api


class ApiCors:
    """Keep public APIs open; credentials are accepted only from frontend origins."""

    def __init__(self, app):
        self.private = CORSMiddleware(
            app,
            allow_origins=frontend_origins(),
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )
        self.public = CORSMiddleware(
            app, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
        )

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        restricted = is_private_api(path)
        if restricted and scope["type"] == "http":

            async def uncached(message):
                if message["type"] == "http.response.start":
                    headers = [(k, v) for k, v in message["headers"] if k != b"cache-control"]
                    message["headers"] = [*headers, (b"cache-control", b"no-store")]
                await send(message)

            await self.private(scope, receive, uncached)
        else:
            await self.public(scope, receive, send)
