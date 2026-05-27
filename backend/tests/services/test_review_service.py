import pytest
from sqlalchemy.orm import Session

from app.services.errors import ConflictError
from app.services.profile_service import save_profile_draft, submit_review
from tests.helpers.factories import draft_payload, register_member


def test_duplicate_submit_review_returns_conflict(db: Session) -> None:
    user, profile = register_member(db)
    experiences, awards = draft_payload()
    save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="First draft",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    first = submit_review(db, profile_id=profile.id, submitter_user_id=user.id)

    assert first.status == "pending"
    with pytest.raises(ConflictError):
        submit_review(db, profile_id=profile.id, submitter_user_id=user.id)
