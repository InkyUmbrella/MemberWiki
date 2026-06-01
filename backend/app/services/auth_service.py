from datetime import timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.enums import UserRole, UserStatus
from app.models.profile import Profile
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthTokenResponse
from app.schemas.user import UserResponse
from app.services.errors import ConflictError, UnauthorizedError, ValidationError
from app.services.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_secret,
    needs_password_upgrade,
    verify_password,
)
from app.services.time import utcnow


def user_to_schema(user: User) -> UserResponse:
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


def register_user(
    db: Session,
    *,
    name: str,
    email: str | None,
    phone: str | None,
    password: str,
) -> AuthTokenResponse:
    # TODO(product): current V1 users.email is NOT NULL, so pure phone registration
    # cannot be persisted until the nullable-email compatibility migration is accepted.
    if not email:
        raise ValidationError("email is required by current V1 database schema")
    if not email and not phone:
        raise ValidationError("email or phone is required")

    existing = db.scalar(
        select(User).where(or_(User.email == email, User.phone == phone if phone else False))
    )
    if existing:
        raise ConflictError("account already exists")

    now = utcnow()
    user = User(
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        display_name=name,
        avatar_url=None,
        role=UserRole.MEMBER.value,
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.flush()

    # Stage-compatible default: create one primary profile for /profiles/me/draft.
    # TODO(product): docs say users 1:N profiles, while /profiles/me/draft implies
    # a current primary profile. Add an explicit primary flag if multi-profile is kept.
    profile = Profile(
        user_id=user.id,
        headline=None,
        bio=None,
        major_tags=None,
        visibility="public",
        published_version_no=0,
        created_at=now,
        updated_at=now,
    )
    db.add(profile)

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_secret(refresh_token),
            expires_at=now + timedelta(days=30),
            revoked_at=None,
            last_used_at=None,
            created_ip=None,
            user_agent=None,
            created_at=now,
        )
    )
    db.flush()
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_to_schema(user),
    )


def login_user(db: Session, *, account: str, password: str) -> AuthTokenResponse:
    user = db.scalar(select(User).where(or_(User.email == account, User.phone == account)))
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("invalid account or password")
    if needs_password_upgrade(user.password_hash):
        user.password_hash = hash_password(password)
    if user.status != UserStatus.ACTIVE.value:
        raise ValidationError("user is disabled")

    now = utcnow()
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_secret(refresh_token),
            expires_at=now + timedelta(days=30),
            revoked_at=None,
            last_used_at=None,
            created_ip=None,
            user_agent=None,
            created_at=now,
        )
    )
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_to_schema(user),
    )
