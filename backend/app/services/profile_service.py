from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.models.achievement import Achievement
from app.models.enums import AchievementCategory, DraftReviewStatus, ReviewRequestStatus, UserRole
from app.models.media_asset import MediaAsset
from app.models.profile import Profile
from app.models.profile_draft import ProfileDraft
from app.models.profile_draft_file import ProfileDraftFile
from app.models.review_request import ReviewRequest
from app.models.user import User
from app.schemas.profile import (
    AwardItem,
    ExperienceItem,
    ProfileDraftResponse,
    PublicProfile,
    SearchResultItem,
)
from app.schemas.review import ReviewTask
from app.schemas.upload import UploadedFile
from app.services.auth_service import user_to_schema
from app.services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.services.serializers import file_url_from_path, parse_date, parse_draft_content, serialize_draft_content
from app.services.time import utcnow


def _uploaded_file(asset: MediaAsset) -> UploadedFile:
    return UploadedFile(
        id=asset.id,
        file_name=asset.file_name,
        file_url=file_url_from_path(asset.file_path),
        mime_type=asset.file_type,
        size=asset.file_size,
        created_at=asset.created_at,
    )


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


def save_profile_draft(
    db: Session,
    *,
    profile_id: int,
    editor_user_id: int,
    bio: str,
    experiences: list[ExperienceItem],
    awards: list[AwardItem],
    proof_file_ids: list[int],
) -> ProfileDraft:
    profile = _require_profile(db, profile_id)
    if profile.user_id != editor_user_id:
        raise ForbiddenError("cannot edit another user's profile")
    now = utcnow()
    max_version = db.scalar(
        select(func.max(ProfileDraft.version_no)).where(ProfileDraft.profile_id == profile_id)
    )
    next_version = (max_version or 0) + 1

    db.execute(
        update(ProfileDraft)
        .where(ProfileDraft.profile_id == profile_id, ProfileDraft.is_latest.is_(True))
        .values(is_latest=False, updated_at=now)
    )

    draft = ProfileDraft(
        profile_id=profile_id,
        editor_user_id=editor_user_id,
        draft_content=serialize_draft_content(bio=bio, experiences=experiences, awards=awards),
        review_status=DraftReviewStatus.DRAFT.value,
        version_no=next_version,
        is_latest=True,
        created_at=now,
        updated_at=now,
    )
    db.add(draft)
    db.flush()

    unique_file_ids = list(dict.fromkeys(proof_file_ids))
    if unique_file_ids:
        assets = db.scalars(
            select(MediaAsset).where(
                MediaAsset.id.in_(unique_file_ids),
                MediaAsset.owner_user_id == editor_user_id,
                MediaAsset.deleted_at.is_(None),
            )
        ).all()
        found_ids = {asset.id for asset in assets}
        missing = set(unique_file_ids) - found_ids
        if missing:
            raise ValidationError(f"invalid proof_file_ids: {sorted(missing)}")
        for asset_id in unique_file_ids:
            db.add(ProfileDraftFile(draft_id=draft.id, media_asset_id=asset_id, created_at=now))

    db.flush()
    return draft


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


def get_my_latest_draft(db: Session, *, profile_id: int, editor_user_id: int) -> ProfileDraftResponse:
    draft = db.scalar(
        select(ProfileDraft).where(
            ProfileDraft.profile_id == profile_id,
            ProfileDraft.editor_user_id == editor_user_id,
            ProfileDraft.is_latest.is_(True),
        )
    )
    if draft is None:
        raise NotFoundError("draft not found")

    content = parse_draft_content(draft.draft_content)
    proof_assets = db.scalars(
        select(MediaAsset)
        .join(ProfileDraftFile, ProfileDraftFile.media_asset_id == MediaAsset.id)
        .where(ProfileDraftFile.draft_id == draft.id, MediaAsset.deleted_at.is_(None))
        .order_by(MediaAsset.created_at.asc())
    ).all()

    return ProfileDraftResponse(
        id=draft.id,
        user_id=draft.editor_user_id,
        review_status=DraftReviewStatus(draft.review_status),
        bio=content["bio"],
        experiences=[ExperienceItem(**item) for item in content["experiences"]],
        awards=[AwardItem(**item) for item in content["awards"]],
        proof_files=[_uploaded_file(asset) for asset in proof_assets],
        updated_at=draft.updated_at,
    )


def get_public_profile(db: Session, *, profile_id: int) -> PublicProfile:
    row = db.execute(
        select(Profile, User)
        .join(User, User.id == Profile.user_id)
        .where(Profile.id == profile_id, Profile.visibility == "public")
    ).one_or_none()
    if row is None:
        raise NotFoundError("profile not found")
    profile, user = row

    achievements = db.scalars(
        select(Achievement)
        .where(Achievement.profile_id == profile_id)
        .order_by(Achievement.category.asc(), Achievement.sort_order.asc(), Achievement.id.asc())
    ).all()
    experiences = [
        ExperienceItem(
            title=item.title,
            organization=item.organization or "",
            description=item.description,
            start_date=item.start_date or item.happened_at,
            end_date=item.end_date,
        )
        for item in achievements
        if item.category == AchievementCategory.EXPERIENCE.value and (item.start_date or item.happened_at)
    ]
    awards = [
        AwardItem(
            name=item.title,
            level=item.award_level,
            year=item.award_year or 1900,
            description=item.description,
        )
        for item in achievements
        if item.category == AchievementCategory.AWARD.value
    ]
    return PublicProfile(
        id=profile.id,
        user=user_to_schema(user),
        bio=profile.bio or "",
        experiences=experiences,
        awards=awards,
        updated_at=profile.updated_at,
    )


def search_members(db: Session, *, keyword: str | None = None, limit: int = 20) -> list[SearchResultItem]:
    award_counts = (
        select(Achievement.profile_id, func.count(Achievement.id).label("award_count"))
        .where(Achievement.category == AchievementCategory.AWARD.value)
        .group_by(Achievement.profile_id)
        .subquery()
    )
    stmt = (
        select(Profile, User, func.coalesce(award_counts.c.award_count, 0))
        .join(User, User.id == Profile.user_id)
        .outerjoin(award_counts, award_counts.c.profile_id == Profile.id)
        .where(Profile.visibility == "public")
    )
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((Profile.bio.like(like)) | (User.display_name.like(like)))
    rows = db.execute(stmt.order_by(Profile.updated_at.desc()).limit(limit)).all()
    results: list[SearchResultItem] = []
    for profile, user, award_count in rows:
        results.append(
            SearchResultItem(
                profile_id=profile.id,
                user_name=user.display_name,
                bio_highlight=profile.bio or "",
                award_count=award_count,
                updated_at=profile.updated_at,
            )
        )
    return results
