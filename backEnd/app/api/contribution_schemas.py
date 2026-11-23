"""Public contribution and private review response contracts."""

from typing import Literal
from uuid import UUID
from pydantic import BaseModel

from contribution.models import ContributionField, ContributionPayload, Kind, Operation

ReviewStatus = Literal["pending", "approved", "rejected", "held", "duplicate", "reverted"]
ReviewFilter = ReviewStatus | Literal["all"]
ContributionValue = str | int | list[str] | None


class RecordLocator(BaseModel):
    artist_id: int | None = None
    ann_song_id: int | None = None
    ann_id: int | None = None
    amq_song_id: int | None = None


class RecordDescription(BaseModel):
    label: str
    detail: str
    locator: RecordLocator
    names: list[str | None]
    type: Literal["person", "group", "choir"] | None = None
    disambiguation: str | None = None
    anime_label: str | None = None
    song_type: int | None = None
    song_number: int | None = None


class ContributionTarget(RecordDescription):
    id: UUID
    kind: Kind
    values: dict[ContributionField, ContributionValue]
    versions: dict[ContributionField, int]


class SubmissionReceipt(BaseModel):
    submission_id: int
    change_count: int


class ReviewSummary(BaseModel):
    id: int
    contributor_name: str
    comment: str
    submitted_at: str
    change_count: int


class ReviewChange(BaseModel):
    id: int
    target_id: UUID
    field: ContributionField
    operation: Operation
    proposed_value: ContributionPayload
    reviewed_value: ContributionPayload
    review_status: ReviewStatus
    review_version: int
    target: RecordDescription
    active_value: ContributionValue
    planned_value: ContributionValue
    field_revision: int
    latest_approved_revision: int
    conflict: str | None
    warnings: list[str]
    event_count: int


class ReviewSubmission(ReviewSummary):
    changes: list[ReviewChange]


class ReviewQueue(BaseModel):
    submissions: list[ReviewSummary]
    next_before: int | None
    counts: dict[ReviewStatus, int]
    loaded_revision: int
    latest_revision: int
    waiting_for_restart: int
    issue_count: int


class ReviewEvent(BaseModel):
    id: int
    reviewer_name: str
    action: Literal["approve", "reject", "hold", "duplicate", "revert"]
    reviewed_value: ContributionPayload | None
    comment: str
    created_at: str


class ReviewHistory(BaseModel):
    events: list[ReviewEvent]
    total: int


class ReviewIssue(BaseModel):
    approved_revision: int
    target: RecordDescription
    reason: str


class ReviewIssues(BaseModel):
    issues: list[ReviewIssue]
    total: int


class DecisionReceipt(BaseModel):
    saved: int


class RevertReceipt(BaseModel):
    saved: bool
