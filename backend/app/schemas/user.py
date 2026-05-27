from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import UserRole


class UserResponse(BaseModel):
    id: int
    name: str = Field(description="Mapped from users.display_name")
    email: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: UserRole
    created_at: datetime
    updated_at: datetime | None = None
