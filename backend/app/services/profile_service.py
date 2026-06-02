from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.error_codes import ProfileErrors
from app.core.result import Result
from app.models.achievement import Achievement
from app.models.enums import AchievementCategory, DraftReviewStatus
from app.models.media_asset import MediaAsset
from app.models.profile import Profile
from app.models.profile_draft import ProfileDraft
from app.models.profile_draft_file import ProfileDraftFile
from app.models.user import User
from app.schemas.profile import (
    AwardItem,
    ExperienceItem,
    ProfileDraftResponse,
    PublicProfile,
)
from app.schemas.upload import UploadedFile
from app.services.serializers import (
    file_url_from_path,
    parse_draft_content,
    serialize_draft_content,
    user_to_schema,
)
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


def _require_profile(db: Session, profile_id: int) -> Result[Profile]:
    profile = db.get(Profile, profile_id)
    if profile is None:
        return Result.failure(ProfileErrors.NOT_FOUND)
    return Result.success(profile)


def get_primary_profile(db: Session, user_id: int) -> Result[Profile]:
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id).order_by(Profile.id.asc()))
    if profile is None:
        return Result.failure(ProfileErrors.NOT_FOUND)
    return Result.success(profile)


def save_profile_draft(
    db: Session,
    *,
    profile_id: int,
    editor_user_id: int,
    bio: str,
    experiences: list[ExperienceItem],
    awards: list[AwardItem],
    proof_file_ids: list[int],
) -> Result[ProfileDraft]:
    profile_result = _require_profile(db, profile_id)
    if not profile_result.ok:
        return profile_result  # pyright: ignore[reportReturnType]
    profile = profile_result.unwrap()
    if profile.user_id != editor_user_id:
        return Result.failure(ProfileErrors.CANNOT_EDIT_OTHERS)
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
            return Result.failure(ProfileErrors.INVALID_PROOF_FILES)
        for asset_id in unique_file_ids:
            db.add(ProfileDraftFile(draft_id=draft.id, media_asset_id=asset_id, created_at=now))

    db.flush()
    return Result.success(draft)


def get_my_latest_draft(db: Session, *, profile_id: int, editor_user_id: int) -> Result[ProfileDraftResponse]:
    draft = db.scalar(
        select(ProfileDraft).where(
            ProfileDraft.profile_id == profile_id,
            ProfileDraft.editor_user_id == editor_user_id,
            ProfileDraft.is_latest.is_(True),
        )
    )
    if draft is None:
        return Result.failure(ProfileErrors.DRAFT_NOT_FOUND)

    content = parse_draft_content(draft.draft_content)
    proof_assets = db.scalars(
        select(MediaAsset)
        .join(ProfileDraftFile, ProfileDraftFile.media_asset_id == MediaAsset.id)
        .where(ProfileDraftFile.draft_id == draft.id, MediaAsset.deleted_at.is_(None))
        .order_by(MediaAsset.created_at.asc())
    ).all()

    return Result.success(ProfileDraftResponse(
        id=draft.id,
        user_id=draft.editor_user_id,
        review_status=DraftReviewStatus(draft.review_status),
        bio=content["bio"],
        experiences=[ExperienceItem(**item) for item in content["experiences"]],
        awards=[AwardItem(**item) for item in content["awards"]],
        proof_files=[_uploaded_file(asset) for asset in proof_assets],
        updated_at=draft.updated_at,
    ))


def get_public_profile(db: Session, *, profile_id: int) -> Result[PublicProfile]:
    row = db.execute(
        select(Profile, User)
        .join(User, User.id == Profile.user_id)
        .where(Profile.id == profile_id, Profile.visibility == "public")
    ).one_or_none()
    if row is None:
        return Result.failure(ProfileErrors.NOT_FOUND)
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
            start_date=item.start_date or item.happened_at,  # pyright: ignore[reportArgumentType]
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
    return Result.success(PublicProfile(
        id=profile.id,
        user=user_to_schema(user),
        bio=profile.bio or "",
        experiences=experiences,
        awards=awards,
        updated_at=profile.updated_at,
    ))
