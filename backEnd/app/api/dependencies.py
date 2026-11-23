"""Typed application resources and access requirements for HTTP handlers."""

from typing import Annotated
from fastapi import Depends, Request

from api.access import require_origin, require_session
from catalog.models import Catalog
from api.response_cache import CachedResponses
from api.schemas import DatabaseStats
from contribution.service import ContributionService


def get_catalog(request: Request) -> Catalog:
    return request.app.state.catalog


def get_contributions(request: Request) -> ContributionService:
    return request.app.state.contribution


def require_log_access(request: Request) -> str:
    return require_session(request, "log")


def require_reviewer(request: Request) -> str:
    return require_session(request, "review")


def require_review_write(request: Request, name: Annotated[str, Depends(require_reviewer)]) -> str:
    require_origin(request)
    return name


CatalogDependency = Annotated[Catalog, Depends(get_catalog)]
ContributionDependency = Annotated[ContributionService, Depends(get_contributions)]
ReviewerWrite = Annotated[str, Depends(require_review_write)]


def get_cached_responses(request: Request) -> CachedResponses:
    return request.app.state.cached_responses


def get_database_stats(request: Request) -> DatabaseStats:
    return request.app.state.database_stats


CachedResponsesDependency = Annotated[CachedResponses, Depends(get_cached_responses)]
StatsDependency = Annotated[DatabaseStats, Depends(get_database_stats)]
