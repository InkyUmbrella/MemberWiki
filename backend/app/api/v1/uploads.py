from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.errors import raise_for_result
from app.core.log import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.upload import UploadedFile
from app.services.upload_service import (
    create_media_asset,
    soft_delete_media_asset,
    uploaded_file_schema,
)

log = get_logger(__name__)
router = APIRouter()


@router.post("/proof", response_model=UploadedFile, status_code=201)
def create_upload_metadata(
    file_name: str = Form(...),
    file_path: str = Form(...),
    mime_type: str = Form(...),
    size: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadedFile:
    log.info(f"create_upload_metadata: name={file_name} size={size} user={current_user.id}")
    result = create_media_asset(
        db,
        owner_user_id=current_user.id,
        file_name=file_name,
        file_path=file_path,
        file_type=mime_type,
        file_size=size,
    )
    raise_for_result(result)
    db.commit()
    return uploaded_file_schema(result.unwrap())


@router.delete("/{file_id}", status_code=204)
def delete_upload(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    log.info(f"delete_upload: file_id={file_id} user={current_user.id}")
    result = soft_delete_media_asset(db, file_id=file_id, owner_user_id=current_user.id)
    raise_for_result(result)
    db.commit()
