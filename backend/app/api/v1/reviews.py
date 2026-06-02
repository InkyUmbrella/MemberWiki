from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ReviewTask
from app.services import review_service

router = APIRouter()


@router.post("/{review_id}/approve", response_model=ReviewTask)
def approve_review(
    review_id: int,
    payload: dict[str, str] | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewTask:
    task = review_service.approve_review(
        db,
        review_id=review_id,
        reviewer_user_id=current_user.id,
        comment=(payload or {}).get("comment"),
    )
    db.commit()
    return task


@router.post("/{review_id}/reject", response_model=ReviewTask)
def reject_review(
    review_id: int,
    payload: dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewTask:
    task = review_service.reject_review(
        db,
        review_id=review_id,
        reviewer_user_id=current_user.id,
        reason=payload["reason"],
    )
    db.commit()
    return task
