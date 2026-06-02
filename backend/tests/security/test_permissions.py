import pytest
from sqlalchemy.orm import Session

from app.services.errors import ForbiddenError
from app.services.profile_service import save_profile_draft
from app.services.review_service import approve_review, submit_review
from tests.helpers.factories import draft_payload, register_member


def test_cross_user_cannot_edit_or_submit_profile(db: Session) -> None:
    owner, profile = register_member(db)
    other, _ = register_member(db, email="other@example.com")
    experiences, awards = draft_payload()

    with pytest.raises(ForbiddenError):
        save_profile_draft(
            db,
            profile_id=profile.id,
            editor_user_id=other.id,
            bio="Cross edit",
            experiences=experiences,
            awards=awards,
            proof_file_ids=[],
        )

    save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=owner.id,
        bio="Owner draft",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    with pytest.raises(ForbiddenError):
        submit_review(db, profile_id=profile.id, submitter_user_id=other.id)


def test_member_cannot_approve_review(db: Session) -> None:
    user, profile = register_member(db)
    experiences, awards = draft_payload()
    save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="Pending draft",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    review = submit_review(db, profile_id=profile.id, submitter_user_id=user.id)

    with pytest.raises(ForbiddenError):
        approve_review(db, review_id=review.id, reviewer_user_id=user.id, comment="ok")
