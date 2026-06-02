from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.core.log import get_logger
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.serializers import user_to_schema

log = get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    log.info(f"users.me: user_id={current_user.id}")
    return user_to_schema(current_user)
