from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.errors import raise_for_result
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileDraftResponse, PublicProfile, UpsertProfileDraftRequest
from app.schemas.review import ReviewTask
from app.services import profile_service, review_service

router = APIRouter()


@router.get("/me/draft", response_model=ProfileDraftResponse)
def get_my_draft(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileDraftResponse:
    profile_result = profile_service.get_primary_profile(db, current_user.id)
    raise_for_result(profile_result)
    profile = profile_result.unwrap()
    result = profile_service.get_my_latest_draft(db, profile_id=profile.id, editor_user_id=current_user.id)
    raise_for_result(result)
    return result.unwrap()


@router.put("/me/draft", response_model=ProfileDraftResponse)
def put_my_draft(
    payload: UpsertProfileDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileDraftResponse:
    profile_result = profile_service.get_primary_profile(db, current_user.id)
    raise_for_result(profile_result)
    profile = profile_result.unwrap()
    result = profile_service.save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=current_user.id,
        bio=payload.bio,
        experiences=payload.experiences,
        awards=payload.awards,
        proof_file_ids=payload.proof_file_ids,
    )
    raise_for_result(result)
    db.commit()
    draft_result = profile_service.get_my_latest_draft(db, profile_id=profile.id, editor_user_id=current_user.id)
    raise_for_result(draft_result)
    return draft_result.unwrap()


@router.post("/me/submit-review", response_model=ReviewTask, status_code=202)
def submit_my_review(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewTask:
    profile_result = profile_service.get_primary_profile(db, current_user.id)
    raise_for_result(profile_result)
    profile = profile_result.unwrap()
    result = review_service.submit_review(db, profile_id=profile.id, submitter_user_id=current_user.id)
    raise_for_result(result)
    db.commit()
    return result.unwrap()


@router.get("/{profile_id}", response_model=PublicProfile)
def public_profile(profile_id: int, db: Session = Depends(get_db)) -> PublicProfile:
    result = profile_service.get_public_profile(db, profile_id=profile_id)
    raise_for_result(result)
    return result.unwrap()
