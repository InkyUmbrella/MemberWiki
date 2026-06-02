from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import DraftReviewStatus


class ReviewTask(BaseModel):
    id: int
    profile_id: int
    submitter_id: int
    reviewer_id: int | None = None
    status: DraftReviewStatus
    reject_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ApproveReviewRequest(BaseModel):
    comment: str | None = None


class RejectReviewRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ProfileTimelineItem(BaseModel):
    version: int
    status: DraftReviewStatus
    operator_name: str
    comment: str | None = None
    created_at: datetime
