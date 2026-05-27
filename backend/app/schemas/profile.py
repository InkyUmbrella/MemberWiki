from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import DraftReviewStatus
from app.schemas.upload import UploadedFile
from app.schemas.user import UserResponse


class ExperienceItem(BaseModel):
    title: str = Field(max_length=100)
    organization: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    start_date: date
    end_date: date | None = None


class AwardItem(BaseModel):
    name: str = Field(max_length=100)
    level: str | None = Field(default=None, max_length=50)
    year: int = Field(ge=1900, le=2100)
    description: str | None = Field(default=None, max_length=500)


class UpsertProfileDraftRequest(BaseModel):
    bio: str = Field(max_length=2000)
    experiences: list[ExperienceItem]
    awards: list[AwardItem]
    proof_file_ids: list[int] = Field(default_factory=list)


class ProfileDraftResponse(BaseModel):
    id: int
    user_id: int
    review_status: DraftReviewStatus
    bio: str
    experiences: list[ExperienceItem]
    awards: list[AwardItem]
    proof_files: list[UploadedFile] = Field(default_factory=list)
    updated_at: datetime


class PublicProfile(BaseModel):
    id: int
    user: UserResponse
    bio: str
    experiences: list[ExperienceItem]
    awards: list[AwardItem]
    updated_at: datetime


class SearchResultItem(BaseModel):
    profile_id: int
    user_name: str
    bio_highlight: str
    award_count: int
    updated_at: datetime
