"""FastAPI application wiring and startup lifecycle."""

from contextlib import asynccontextmanager
import hashlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from api.log_request_handling import install_request_logging
from api.response_cache import build_cached_responses
from api.search_routes import router as search_router
from api.access import reset_sessions
from api.cors import ApiCors
from api.errors import install_contribution_errors
from api.log_routes import router as log_router
from api.review_routes import router as review_router
from api.schemas import DatabaseStats
from api.contribution_routes import router as contribution_router
from contribution.service import ContributionService
from contribution.store import ContributionStore
from catalog.loader import DATABASE_PATH, load_catalog
from catalog.statistics import build_statistics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the immutable read catalog before accepting requests."""
    reset_sessions()
    contribution_path = Path(__file__).resolve().parent / "data" / "contributions.db"
    app.state.contribution = ContributionService(ContributionStore(contribution_path))
    with DATABASE_PATH.open("rb") as source:
        digest = hashlib.sha256()
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
        fingerprint = digest.hexdigest()
    app.state.catalog = load_catalog(transform=lambda songs, artists: app.state.contribution.apply(songs, artists, fingerprint))
    app.state.cached_responses = build_cached_responses(app.state.catalog)
    app.state.database_stats = DatabaseStats(**build_statistics(app.state.catalog))
    app.state.contribution.complete_load()
    try:
        yield
    finally:
        app.state.catalog = None
        app.state.cached_responses = None
        app.state.database_stats = None
        app.state.contribution = None


# Launch API
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Compress responses > 1000 bytes
)
app.add_middleware(ApiCors)
install_request_logging(app)
install_contribution_errors(app)
app.include_router(search_router)
app.include_router(log_router)
app.include_router(review_router)
app.include_router(contribution_router)
