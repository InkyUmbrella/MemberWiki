from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import UserStatus
from app.models.user import User
from app.services.errors import ForbiddenError, UnauthorizedError
from app.services.security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> User:
    if credentials is None:
        raise UnauthorizedError("authorization header is required")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise UnauthorizedError("invalid or expired access token")
    user_id = payload["sub"]
    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("user not found")
    if user.status != UserStatus.ACTIVE.value:
        raise ForbiddenError("account is disabled")
    return user
