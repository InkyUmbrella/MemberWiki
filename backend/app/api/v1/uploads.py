from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.upload import UploadedFile
from app.services.upload_service import create_media_asset, soft_delete_media_asset, uploaded_file_schema

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
    # Minimal DB integration endpoint. Real multipart file persistence should write
    # to object/local storage first, then call this metadata insertion path.
    asset = create_media_asset(
        db,
        owner_user_id=current_user.id,
        file_name=file_name,
        file_path=file_path,
        file_type=mime_type,
        file_size=size,
    )
    db.commit()
    return uploaded_file_schema(asset)


@router.delete("/{file_id}", status_code=204)
def delete_upload(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    soft_delete_media_asset(db, file_id=file_id, owner_user_id=current_user.id)
    db.commit()
