from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.errors import raise_for_result
from app.core.log import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ApproveReviewRequest, RejectReviewRequest, ReviewTask
from app.services import review_service

log = get_logger(__name__)
router = APIRouter()


@router.post("/{review_id}/approve", response_model=ReviewTask)
def approve_review(
    review_id: int,
    payload: ApproveReviewRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewTask:
    log.info(f"approve_review: review_id={review_id} reviewer={current_user.id}")
    result = review_service.approve_review(
        db,
        review_id=review_id,
        reviewer_user_id=current_user.id,
        comment=payload.comment if payload else None,
    )
    raise_for_result(result)
    db.commit()
    return result.unwrap()


@router.post("/{review_id}/reject", response_model=ReviewTask)
def reject_review(
    review_id: int,
    payload: RejectReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewTask:
    log.info(f"reject_review: review_id={review_id} reviewer={current_user.id}")
    result = review_service.reject_review(
        db,
        review_id=review_id,
        reviewer_user_id=current_user.id,
        reason=payload.reason,
    )
    raise_for_result(result)
    db.commit()
    return result.unwrap()
