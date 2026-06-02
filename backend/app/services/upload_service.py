from sqlalchemy.orm import Session

from app.core.error_codes import UploadErrors
from app.core.log import get_logger
from app.core.result import Result
from app.models.media_asset import MediaAsset
from app.schemas.upload import UploadedFile
from app.services.serializers import file_url_from_path
from app.services.time import utcnow

log = get_logger(__name__)


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
) -> Result[MediaAsset]:
    with log.time(f"create_media_asset: file_name={file_name} {{elapsed}}"):
        if not file_name:
            return Result.failure(UploadErrors.FILE_NAME_REQUIRED)
        if not file_path:
            return Result.failure(UploadErrors.FILE_PATH_REQUIRED)
        if file_size <= 0:
            return Result.failure(UploadErrors.FILE_SIZE_NOT_POSITIVE)

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
        return Result.success(asset)


def soft_delete_media_asset(db: Session, *, file_id: int, owner_user_id: int) -> Result[bool]:
    with log.time(f"soft_delete_media_asset: file_id={file_id} {{elapsed}}"):
        asset = db.get(MediaAsset, file_id)
        if asset is None:
            return Result.failure(UploadErrors.NOT_FOUND)
        if asset.owner_user_id != owner_user_id:
            return Result.failure(UploadErrors.CANNOT_DELETE_OTHERS)
        asset.deleted_at = utcnow()
        db.flush()
        return Result.success(True)
