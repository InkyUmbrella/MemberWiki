import json
from datetime import date
from typing import Any

from app.schemas.profile import AwardItem, ExperienceItem


def _json_default(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def serialize_draft_content(
    *,
    bio: str,
    experiences: list[ExperienceItem | dict[str, Any]],
    awards: list[AwardItem | dict[str, Any]],
) -> str:
    payload = {
        "bio": bio,
        "experiences": [
            item.model_dump() if hasattr(item, "model_dump") else item.dict() if hasattr(item, "dict") else item
            for item in experiences
        ],
        "awards": [
            item.model_dump() if hasattr(item, "model_dump") else item.dict() if hasattr(item, "dict") else item
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
