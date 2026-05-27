import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.media_asset import MediaAsset
from app.models.profile_draft import ProfileDraft
from app.services.profile_service import save_profile_draft
from app.services.security import hash_secret
from app.services.time import utcnow
from tests.helpers.factories import draft_payload, register_member


def test_media_file_size_constraint_and_one_latest_draft(db: Session) -> None:
    user, profile = register_member(db)
    now = utcnow()
    db.add(
        MediaAsset(
            owner_user_id=user.id,
            file_name="bad.txt",
            file_path="bad.txt",
            file_type="text/plain",
            file_size=0,
            ref_type=None,
            ref_id=None,
            checksum_sha256=hash_secret("bad"),
            deleted_at=None,
            created_at=now,
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()

    experiences, awards = draft_payload()
    save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="v1",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="v2",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[],
    )
    latest_count = (
        db.query(ProfileDraft)
        .filter(ProfileDraft.profile_id == profile.id, ProfileDraft.is_latest.is_(True))
        .count()
    )
    assert latest_count == 1
