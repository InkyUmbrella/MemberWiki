from sqlalchemy.orm import Session

from app.models.media_asset import MediaAsset
from app.schemas.upload import UploadedFile
from app.services.errors import ForbiddenError, NotFoundError, ValidationError
from app.services.serializers import file_url_from_path
from app.services.time import utcnow


def uploaded_file_schema(asset: MediaAsset) -> UploadedFile:
    return UploadedFile(
        id=asset.id,
        file_name=asset.file_name,
        file_url=file_url_from_path(asset.file_path),
        mime_type=asset.file_type,
        size=asset.file_size,
        created_at=asset.created_at,
    )


def create_media_asset(
    db: Session,
    *,
    owner_user_id: int,
    file_name: str,
    file_path: str,
    file_type: str,
    file_size: int,
    checksum_sha256: str | None = None,
) -> MediaAsset:
    if not file_name:
        raise ValidationError("file_name is required")
    if not file_path:
        raise ValidationError("file_path is required")
    if file_size <= 0:
        raise ValidationError("file_size must be positive")

    now = utcnow()
    asset = MediaAsset(
        owner_user_id=owner_user_id,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        ref_type=None,
        ref_id=None,
        checksum_sha256=checksum_sha256,
        deleted_at=None,
        created_at=now,
    )
    db.add(asset)
    db.flush()
    return asset


def soft_delete_media_asset(db: Session, *, file_id: int, owner_user_id: int) -> bool:
    asset = db.get(MediaAsset, file_id)
    if asset is None:
        raise NotFoundError("file not found")
    if asset.owner_user_id != owner_user_id:
        raise ForbiddenError("cannot delete another user's file")
    asset.deleted_at = utcnow()
    db.flush()
    return True
