import json
from collections.abc import Sequence
from datetime import date
from typing import Any

from app.schemas.profile import AwardItem, ExperienceItem
from app.schemas.user import UserResponse


def _json_default(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def serialize_draft_content(
    *,
    bio: str,
    experiences: Sequence[ExperienceItem],
    awards: Sequence[AwardItem],
) -> str:
    payload = {
        "bio": bio,
        "experiences": [
            item.model_dump()  # pyright: ignore[reportAttributeAccessIssue]
            for item in experiences
        ],
        "awards": [
            item.model_dump()  # pyright: ignore[reportAttributeAccessIssue]
            for item in awards
        ],
    }
    return json.dumps(payload, ensure_ascii=False, default=_json_default)


def parse_draft_content(value: str) -> dict[str, Any]:
    payload = json.loads(value)
    return {
        "bio": payload.get("bio") or "",
        "experiences": payload.get("experiences") or [],
        "awards": payload.get("awards") or [],
    }


def file_url_from_path(file_path: str) -> str:
    if file_path.startswith(("http://", "https://", "/")):
        return file_path
    return f"/uploads/{file_path.lstrip('/')}"


def parse_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)


def user_to_schema(user: Any) -> UserResponse:
    from app.models.enums import UserRole

    return UserResponse(
        id=user.id,
        name=user.display_name,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=UserRole(user.role),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
