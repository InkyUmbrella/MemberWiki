from sqlalchemy.orm import Session

from app.services.profile_service import save_profile_draft
from app.services.review_service import approve_review, submit_review
from tests.helpers.factories import draft_payload, register_member


def test_cross_user_cannot_edit_or_submit_profile(db: Session) -> None:
    owner, profile = register_member(db)
    other, _ = register_member(db, email="other@example.com")
    experiences, awards = draft_payload()

    result = save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=other.id,
        bio="Cross edit",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    assert not result.ok
    assert result.code == "FORBIDDEN"

    owner_result = save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=owner.id,
        bio="Owner draft",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    assert owner_result.ok
    submit_result = submit_review(db, profile_id=profile.id, submitter_user_id=other.id)
    assert not submit_result.ok
    assert submit_result.code == "FORBIDDEN"


def test_member_cannot_approve_review(db: Session) -> None:
    user, profile = register_member(db)
    experiences, awards = draft_payload()
    draft_result = save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="Pending draft",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    assert draft_result.ok
    review_result = submit_review(db, profile_id=profile.id, submitter_user_id=user.id)
    assert review_result.ok
    review = review_result.unwrap()

    approve_result = approve_review(db, review_id=review.id, reviewer_user_id=user.id, comment="ok")
    assert not approve_result.ok
    assert approve_result.code == "FORBIDDEN"
