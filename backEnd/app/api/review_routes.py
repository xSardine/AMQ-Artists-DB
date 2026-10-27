"""Reviewer access and protected contribution review endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from api.access import create_session, logout, rate_limit, require_origin, session, verify_password
from api.access_schemas import AccessSession, LogoutResult, ReviewLogin
from api.contribution_schemas import (
    DecisionReceipt,
    RevertReceipt,
    ReviewFilter,
    ReviewHistory,
    ReviewIssues,
    ReviewQueue,
    ReviewSubmission,
)
from api.dependencies import (
    CatalogDependency,
    ContributionDependency,
    ReviewerWrite,
    require_reviewer,
)
from contribution.models import SQLITE_MAX_INTEGER, Decisions, Kind, Revert
from settings import setting

SqlitePathId = Annotated[int, Path(gt=0, le=SQLITE_MAX_INTEGER)]
SqliteOffset = Annotated[int, Query(ge=0, le=SQLITE_MAX_INTEGER)]

router = APIRouter(prefix="/api/review", include_in_schema=False)
protected = APIRouter(dependencies=[Depends(require_reviewer)])


@router.post("/login", response_model=AccessSession)
def login(request: Request, response: Response, data: ReviewLogin):
    require_origin(request)
    rate_limit(request, "review-login", 5, 300)
    verify_password(data.password, setting("REVIEW_PASSWORD"))
    return create_session(request, response, "review", data.name)


@router.get("/session", response_model=AccessSession)
def current_session(request: Request, response: Response):
    return session(request, response, "review")


@router.post("/logout", response_model=LogoutResult)
def end_session(request: Request, response: Response):
    return logout(request, response, "review")


@protected.get("/submissions", response_model=ReviewQueue)
def queue(
    catalog: CatalogDependency,
    contributions: ContributionDependency,
    status: ReviewFilter = "pending",
    before: int = Query(default=SQLITE_MAX_INTEGER, gt=0, le=SQLITE_MAX_INTEGER),
    limit: int = Query(default=20, ge=1, le=50),
    kind: Kind | None = None,
    search: str = Query(default="", max_length=200),
):
    return contributions.queue(catalog, status, before, limit, kind, search)


@protected.get(
    "/submissions/{submission_id}",
    response_model=ReviewSubmission,
    response_model_exclude_unset=True,
)
def submission(
    catalog: CatalogDependency,
    contributions: ContributionDependency,
    submission_id: SqlitePathId,
):
    return contributions.submission(catalog, submission_id)


@protected.get("/changes/{change_id}/history", response_model=ReviewHistory)
def history(
    contributions: ContributionDependency,
    change_id: SqlitePathId,
    offset: SqliteOffset = 0,
    limit: int = Query(default=10, ge=1, le=50),
):
    return contributions.history(change_id, offset, limit)


@protected.get("/issues", response_model=ReviewIssues, response_model_exclude_unset=True)
def issues(
    contributions: ContributionDependency,
    offset: SqliteOffset = 0,
    limit: int = Query(default=10, ge=1, le=50),
):
    return contributions.issues(offset, limit)


@protected.post("/decisions", response_model=DecisionReceipt)
def decide(
    catalog: CatalogDependency,
    contributions: ContributionDependency,
    reviewer: ReviewerWrite,
    data: Decisions,
):
    contributions.decide(data.decisions, reviewer, catalog)
    return {"saved": len(data.decisions)}


@protected.post("/revert", response_model=RevertReceipt)
def revert(
    catalog: CatalogDependency,
    contributions: ContributionDependency,
    reviewer: ReviewerWrite,
    data: Revert,
):
    contributions.revert(data, reviewer, catalog)
    return {"saved": True}


router.include_router(protected)
