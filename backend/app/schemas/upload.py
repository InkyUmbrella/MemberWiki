from datetime import datetime

from pydantic import BaseModel


class UploadedFile(BaseModel):
    id: int
    file_name: str
    file_url: str
    mime_type: str
    size: int
    created_at: datetime
