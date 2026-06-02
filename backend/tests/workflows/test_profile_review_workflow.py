from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.services.profile_service import (
    get_public_profile,
    save_profile_draft,
)
from app.services.review_service import approve_review, submit_review
from tests.helpers.factories import draft_payload, register_admin, register_member


def test_approve_review_publishes_public_profile(db: Session) -> None:
    user, profile = register_member(db)
    admin, _ = register_admin(db)
    experiences, awards = draft_payload()
    draft_result = save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="Published biography",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    assert draft_result.ok
    draft = draft_result.unwrap()
    review_result = submit_review(db, profile_id=profile.id, submitter_user_id=user.id)
    assert review_result.ok
    review = review_result.unwrap()

    approve_result = approve_review(db, review_id=review.id, reviewer_user_id=admin.id, comment="complete")
    assert approve_result.ok
    public_result = get_public_profile(db, profile_id=profile.id)
    assert public_result.ok
    public_profile = public_result.unwrap()

    assert public_profile.bio == "Published biography"
    assert public_profile.experiences[0].title == "Backend Lead"
    assert public_profile.awards[0].name == "Innovation Prize"
    assert db.get(Profile, profile.id).published_version_no == draft.version_no
