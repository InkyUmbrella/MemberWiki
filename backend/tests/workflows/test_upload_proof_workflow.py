from sqlalchemy.orm import Session

from app.services.profile_service import get_my_latest_draft, save_profile_draft
from app.services.upload_service import soft_delete_media_asset
from tests.helpers.factories import create_proof_asset, draft_payload, register_member


def test_deleted_upload_is_not_returned_in_proof_files(db: Session) -> None:
    user, profile = register_member(db)
    asset = create_proof_asset(db, owner_user_id=user.id)
    experiences, awards = draft_payload()
    save_draft_result = save_profile_draft(
        db,
        profile_id=profile.id,
        editor_user_id=user.id,
        bio="Draft with proof",
        experiences=experiences,
        awards=awards,
        proof_file_ids=[asset.id],
    )
    assert save_draft_result.ok

    before_result = get_my_latest_draft(db, profile_id=profile.id, editor_user_id=user.id)
    assert before_result.ok
    before_delete = before_result.unwrap()
    assert len(before_delete.proof_files) == 1

    delete_result = soft_delete_media_asset(db, file_id=asset.id, owner_user_id=user.id)
    assert delete_result.ok

    after_result = get_my_latest_draft(db, profile_id=profile.id, editor_user_id=user.id)
    assert after_result.ok
    after_delete = after_result.unwrap()
    assert after_delete.proof_files == []
