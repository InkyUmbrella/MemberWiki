from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileDraftResponse, PublicProfile, UpsertProfileDraftRequest
from app.schemas.review import ReviewTask
from app.services import profile_service
from app.services.errors import NotFoundError

router = APIRouter()


def _current_primary_profile(db: Session, user_id: int) -> Profile:
    # Stage-compatible implementation for /profiles/me/draft.
    # TODO(product): docs permit users 1:N profiles; add explicit primary-profile
    # semantics before exposing multiple profiles per member.
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id).order_by(Profile.id.asc()))
    if profile is None:
        raise NotFoundError("profile not found")
    return profile


@router.get("/me/draft", response_model=ProfileDraftResponse)
def get_my_draft(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileDraftResponse:
    profile = _current_primary_profile(db, current_user.id)
    return profile_service.get_my_latest_draft(db, profile_id=profile.id, editor_user_id=current_user.id)


@router.put("/me/draft", response_model=ProfileDraftResponse)
def put_my_draft(
    payload: UpsertProfileDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileDraftResponse:
    profile = _current_primary_profile(db, current_user.id)
    profile_service.save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=current_user.id,
        bio=payload.bio,
        experiences=payload.experiences,
        awards=payload.awards,
        proof_file_ids=payload.proof_file_ids,
    )
    db.commit()
    return profile_service.get_my_latest_draft(db, profile_id=profile.id, editor_user_id=current_user.id)


@router.post("/me/submit-review", response_model=ReviewTask, status_code=202)
def submit_my_review(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewTask:
    profile = _current_primary_profile(db, current_user.id)
    task = profile_service.submit_review(db, profile_id=profile.id, submitter_user_id=current_user.id)
    db.commit()
    return task


@router.get("/{profile_id}", response_model=PublicProfile)
def public_profile(profile_id: int, db: Session = Depends(get_db)) -> PublicProfile:
    return profile_service.get_public_profile(db, profile_id=profile_id)
