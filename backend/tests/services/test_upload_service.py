import pytest
from sqlalchemy.orm import Session

from app.services.errors import ForbiddenError, NotFoundError
from app.services.upload_service import soft_delete_media_asset
from tests.helpers.factories import create_proof_asset, register_member


def test_upload_delete_reports_forbidden_and_not_found(db: Session) -> None:
    user, _ = register_member(db)
    other, _ = register_member(db, email="other-delete@example.com")
    asset = create_proof_asset(
        db,
        owner_user_id=user.id,
        file_path="proofs/delete-guard.pdf",
    )

    with pytest.raises(ForbiddenError):
        soft_delete_media_asset(db, file_id=asset.id, owner_user_id=other.id)
    with pytest.raises(NotFoundError):
        soft_delete_media_asset(db, file_id=999999, owner_user_id=user.id)
