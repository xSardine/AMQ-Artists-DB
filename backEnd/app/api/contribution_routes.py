"""Public catalog lookup and contribution submission endpoints."""

from uuid import UUID
from fastapi import APIRouter, Query, Request

from api.access import rate_limit
from api.contribution_schemas import ContributionTarget, SubmissionReceipt
from api.dependencies import CatalogDependency, ContributionDependency
from contribution.models import Kind, SubmissionInput

router = APIRouter(prefix="/api", include_in_schema=False)


@router.get(
    '/contribution-targets',
    response_model=list[ContributionTarget],
    response_model_exclude_unset=True,
)
def targets(
    request: Request,
    catalog: CatalogDependency,
    contributions: ContributionDependency,
    kind: Kind,
    search: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=30, ge=1, le=50),
):
    rate_limit(request, "target-lookup", 120, 60)
    return contributions.search_targets(catalog, kind, search, limit)


@router.get(
    '/contribution-targets/{target_id}',
    response_model=ContributionTarget,
    response_model_exclude_unset=True,
)
def target(
    request: Request,
    catalog: CatalogDependency,
    contributions: ContributionDependency,
    target_id: UUID,
):
    rate_limit(request, "target-lookup", 120, 60)
    return contributions.target(catalog, str(target_id))


@router.post('/contributions', status_code=201, response_model=SubmissionReceipt)
def contribute(
    request: Request,
    catalog: CatalogDependency,
    contributions: ContributionDependency,
    data: SubmissionInput,
):
    rate_limit(request, "contribute", 20, 600)
    submission_id = contributions.submit(data, catalog)
    return {"submission_id": submission_id, "change_count": len(data.changes)}
