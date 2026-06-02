from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.error_codes import AuthErrors
from app.core.errors import AppError
from app.db.session import get_db
from app.models.enums import UserStatus
from app.models.user import User
from app.services.security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> User:
    if credentials is None:
        raise AppError(AuthErrors.AUTH_HEADER_REQUIRED.code, AuthErrors.AUTH_HEADER_REQUIRED.message, status_code=401)
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise AppError(AuthErrors.INVALID_TOKEN.code, AuthErrors.INVALID_TOKEN.message, status_code=401)
    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if user is None:
        raise AppError(AuthErrors.USER_NOT_FOUND.code, AuthErrors.USER_NOT_FOUND.message, status_code=401)
    if user.status != UserStatus.ACTIVE.value:
        raise AppError(AuthErrors.USER_DISABLED.code, AuthErrors.USER_DISABLED.message, status_code=403)
    return user
