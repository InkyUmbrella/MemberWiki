from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.error_codes import ProfileErrors, ReviewErrors
from app.core.log import get_logger
from app.core.result import Result
from app.models.achievement import Achievement
from app.models.enums import AchievementCategory, DraftReviewStatus, ReviewRequestStatus, UserRole
from app.models.profile import Profile
from app.models.profile_draft import ProfileDraft
from app.models.review_request import ReviewRequest
from app.models.user import User
from app.schemas.review import ReviewTask
from app.services.serializers import parse_date, parse_draft_content
from app.services.time import utcnow

log = get_logger(__name__)


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


def _require_profile(db: Session, profile_id: int) -> Result[Profile]:
    profile = db.get(Profile, profile_id)
    if profile is None:
        return Result.failure(ProfileErrors.NOT_FOUND)
    return Result.success(profile)


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


def submit_review(db: Session, *, profile_id: int, submitter_user_id: int) -> Result[ReviewTask]:
    with log.time(f"submit_review: profile_id={profile_id} {{elapsed}}"):
        profile_result = _require_profile(db, profile_id)
        if not profile_result.ok:
            return profile_result  # pyright: ignore[reportReturnType]
        profile = profile_result.unwrap()
        if profile.user_id != submitter_user_id:
            return Result.failure(ReviewErrors.CANNOT_SUBMIT_OTHERS)
        pending = db.scalar(
            select(ReviewRequest).where(
                ReviewRequest.profile_id == profile_id,
                ReviewRequest.status == ReviewRequestStatus.PENDING.value,
            )
        )
        if pending:
            return Result.failure(ReviewErrors.ALREADY_PENDING)

        draft = db.scalar(
            select(ProfileDraft).where(
                ProfileDraft.profile_id == profile_id,
                ProfileDraft.editor_user_id == submitter_user_id,
                ProfileDraft.is_latest.is_(True),
            )
        )
        if draft is None:
            return Result.failure(ProfileErrors.DRAFT_NOT_FOUND)
        if draft.review_status == DraftReviewStatus.PENDING.value:
            return Result.failure(ReviewErrors.DRAFT_ALREADY_PENDING)

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
        return Result.success(_review_task(review))


def approve_review(
    db: Session,
    *,
    review_id: int,
    reviewer_user_id: int,
    comment: str | None = None,
) -> Result[ReviewTask]:
    with log.time(f"approve_review: review_id={review_id} {{elapsed}}"):
        reviewer = db.get(User, reviewer_user_id)
        if reviewer is None or reviewer.role != UserRole.ADMIN.value:
            return Result.failure(ReviewErrors.ADMIN_ONLY)

        review = db.get(ReviewRequest, review_id)
        if review is None:
            return Result.failure(ReviewErrors.NOT_FOUND)
        if review.status != ReviewRequestStatus.PENDING.value:
            return Result.failure(ReviewErrors.NOT_PENDING)
        if review.draft_id is None:
            return Result.failure(ReviewErrors.NO_DRAFT_ID)

        draft = db.get(ProfileDraft, review.draft_id)
        profile = db.get(Profile, review.profile_id)
        if draft is None or profile is None:
            return Result.failure(ReviewErrors.DRAFT_OR_PROFILE_NOT_FOUND)

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
        sp = db.begin_nested()
        try:
            _rebuild_achievements(db, profile_id=profile.id, content=content)
        except Exception:
            sp.rollback()
            raise
        db.flush()
        return Result.success(_review_task(review))


def reject_review(
    db: Session,
    *,
    review_id: int,
    reviewer_user_id: int,
    reason: str,
) -> Result[ReviewTask]:
    with log.time(f"reject_review: review_id={review_id} {{elapsed}}"):
        reviewer = db.get(User, reviewer_user_id)
        if reviewer is None or reviewer.role != UserRole.ADMIN.value:
            return Result.failure(ReviewErrors.ADMIN_ONLY_REJECT)

        review = db.get(ReviewRequest, review_id)
        if review is None:
            return Result.failure(ReviewErrors.NOT_FOUND)
        if review.status != ReviewRequestStatus.PENDING.value:
            return Result.failure(ReviewErrors.NOT_PENDING)

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
        return Result.success(_review_task(review))
