from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.achievement import Achievement
from app.models.enums import AchievementCategory, DraftReviewStatus, ReviewRequestStatus, UserRole
from app.models.profile import Profile
from app.models.profile_draft import ProfileDraft
from app.models.review_request import ReviewRequest
from app.models.user import User
from app.schemas.review import ReviewTask
from app.services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.services.serializers import parse_date, parse_draft_content
from app.services.time import utcnow


def _review_task(review: ReviewRequest) -> ReviewTask:
    return ReviewTask(
        id=review.id,
        profile_id=review.profile_id,
        submitter_id=review.submitter_user_id,
        reviewer_id=review.reviewer_user_id,
        status=DraftReviewStatus(review.status),
        reject_reason=review.reject_reason,
        created_at=review.submitted_at,
        updated_at=review.updated_at,
    )


def _require_profile(db: Session, profile_id: int) -> Profile:
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise NotFoundError("profile not found")
    return profile


def submit_review(db: Session, *, profile_id: int, submitter_user_id: int) -> ReviewTask:
    profile = _require_profile(db, profile_id)
    if profile.user_id != submitter_user_id:
        raise ForbiddenError("cannot submit another user's profile")
    pending = db.scalar(
        select(ReviewRequest).where(
            ReviewRequest.profile_id == profile_id,
            ReviewRequest.status == ReviewRequestStatus.PENDING.value,
        )
    )
    if pending:
        raise ConflictError("profile already has a pending review")

    draft = db.scalar(
        select(ProfileDraft).where(
            ProfileDraft.profile_id == profile_id,
            ProfileDraft.editor_user_id == submitter_user_id,
            ProfileDraft.is_latest.is_(True),
        )
    )
    if draft is None:
        raise NotFoundError("latest draft not found")
    if draft.review_status == DraftReviewStatus.PENDING.value:
        raise ConflictError("latest draft is already pending")

    now = utcnow()
    draft.review_status = DraftReviewStatus.PENDING.value
    draft.updated_at = now
    review = ReviewRequest(
        profile_id=profile_id,
        draft_id=draft.id,
        submitter_user_id=submitter_user_id,
        reviewer_user_id=None,
        status=ReviewRequestStatus.PENDING.value,
        change_payload=draft.draft_content,
        review_comment=None,
        reject_reason=None,
        submitted_at=now,
        reviewed_at=None,
        updated_at=now,
    )
    db.add(review)
    db.flush()
    return _review_task(review)


def _rebuild_achievements(db: Session, *, profile_id: int, content: dict[str, Any]) -> None:
    now = utcnow()
    db.execute(delete(Achievement).where(Achievement.profile_id == profile_id))

    for index, item in enumerate(content["experiences"]):
        start_date = parse_date(item.get("start_date"))
        end_date = parse_date(item.get("end_date"))
        db.add(
            Achievement(
                profile_id=profile_id,
                category=AchievementCategory.EXPERIENCE.value,
                title=item["title"],
                organization=item.get("organization"),
                description=item.get("description"),
                start_date=start_date,
                end_date=end_date,
                award_level=None,
                award_year=None,
                happened_at=start_date,
                sort_order=index,
                created_at=now,
                updated_at=now,
            )
        )

    for index, item in enumerate(content["awards"]):
        db.add(
            Achievement(
                profile_id=profile_id,
                category=AchievementCategory.AWARD.value,
                title=item["name"],
                organization=None,
                description=item.get("description"),
                start_date=None,
                end_date=None,
                award_level=item.get("level"),
                award_year=item.get("year"),
                happened_at=None,
                sort_order=index,
                created_at=now,
                updated_at=now,
            )
        )


def approve_review(
    db: Session,
    *,
    review_id: int,
    reviewer_user_id: int,
    comment: str | None = None,
) -> ReviewTask:
    reviewer = db.get(User, reviewer_user_id)
    if reviewer is None or reviewer.role != UserRole.ADMIN.value:
        raise ForbiddenError("only admin can approve reviews")

    review = db.get(ReviewRequest, review_id)
    if review is None:
        raise NotFoundError("review not found")
    if review.status != ReviewRequestStatus.PENDING.value:
        raise ConflictError("review is not pending")
    if review.draft_id is None:
        raise ValidationError("review has no draft_id")

    draft = db.get(ProfileDraft, review.draft_id)
    profile = db.get(Profile, review.profile_id)
    if draft is None or profile is None:
        raise NotFoundError("review draft or profile not found")

    now = utcnow()
    content = parse_draft_content(review.change_payload)
    review.status = ReviewRequestStatus.APPROVED.value
    review.reviewer_user_id = reviewer_user_id
    review.review_comment = comment
    review.reviewed_at = now
    review.updated_at = now

    draft.review_status = DraftReviewStatus.APPROVED.value
    draft.updated_at = now

    profile.bio = content["bio"]
    profile.published_version_no = draft.version_no
    profile.updated_at = now
    _rebuild_achievements(db, profile_id=profile.id, content=content)
    db.flush()
    return _review_task(review)


def reject_review(
    db: Session,
    *,
    review_id: int,
    reviewer_user_id: int,
    reason: str,
) -> ReviewTask:
    reviewer = db.get(User, reviewer_user_id)
    if reviewer is None or reviewer.role != UserRole.ADMIN.value:
        raise ForbiddenError("only admin can reject reviews")

    review = db.get(ReviewRequest, review_id)
    if review is None:
        raise NotFoundError("review not found")
    if review.status != ReviewRequestStatus.PENDING.value:
        raise ConflictError("review is not pending")

    now = utcnow()
    review.status = ReviewRequestStatus.REJECTED.value
    review.reviewer_user_id = reviewer_user_id
    review.reject_reason = reason
    review.reviewed_at = now
    review.updated_at = now

    if review.draft_id is not None:
        draft = db.get(ProfileDraft, review.draft_id)
        if draft:
            draft.review_status = DraftReviewStatus.REJECTED.value
            draft.updated_at = now

    db.flush()
    return _review_task(review)
