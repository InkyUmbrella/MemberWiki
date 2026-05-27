from sqlalchemy.orm import Session

from app.services.profile_service import get_my_latest_draft, save_profile_draft
from tests.helpers.factories import create_proof_asset, draft_payload, register_member


def test_duplicate_proof_file_ids_are_deduplicated(db: Session) -> None:
    user, profile = register_member(db)
    asset = create_proof_asset(
        db,
        owner_user_id=user.id,
        file_path="proofs/dedupe-proof.pdf",
    )
    experiences, awards = draft_payload()

    save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="Draft with duplicate proof IDs",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[asset.id, asset.id],
    )

    latest = get_my_latest_draft(db, profile_id=profile.id, editor_user_id=user.id)
    assert [file.id for file in latest.proof_files] == [asset.id]
