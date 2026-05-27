from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.errors import ForbiddenError, NotFoundError


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None, alias="X-User-ID"),
) -> User:
    # Minimal integration hook. Replace with JWT bearer parsing when auth is implemented.
    if x_user_id is None:
        raise ForbiddenError("X-User-ID is required in development mode")
    user = db.get(User, x_user_id)
    if user is None:
        raise NotFoundError("current user not found")
    return user
