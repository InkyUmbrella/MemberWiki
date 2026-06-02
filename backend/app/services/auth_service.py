import uuid
from datetime import timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.error_codes import AuthErrors
from app.core.log import get_logger
from app.core.result import Result
from app.models.enums import UserRole, UserStatus
from app.models.profile import Profile
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthTokenResponse
from app.services.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_secret,
    needs_password_upgrade,
    verify_password,
)
from app.services.serializers import user_to_schema
from app.services.time import utcnow

log = get_logger(__name__)


def register_user(
    db: Session,
    *,
    name: str,
    email: str | None,
    phone: str | None,
    password: str,
) -> Result[AuthTokenResponse]:
    with log.time(f"register_user: email={email} {{elapsed}}"):
        if not email:
            return Result.failure(AuthErrors.EMAIL_REQUIRED)
        if not email and not phone:
            return Result.failure(AuthErrors.EMAIL_OR_PHONE_REQUIRED)

        existing = db.scalar(
            select(User).where(
                or_(User.email == email, User.phone == phone) if phone else (User.email == email)
            )
        )
        if existing:
            return Result.failure(AuthErrors.ACCOUNT_EXISTS)

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
        log.info(f"register_user: user_id={user.id} created")

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
        family = uuid.uuid4().hex
        db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_secret(refresh_token),
                family=family,
                expires_at=now + timedelta(days=30),
                revoked_at=None,
                last_used_at=None,
                created_ip=None,
                user_agent=None,
                created_at=now,
            )
        )
        db.flush()
        log.info(f"register_user: tokens issued user_id={user.id}")
        return Result.success(AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_to_schema(user),
        ))


def login_user(db: Session, *, account: str, password: str) -> Result[AuthTokenResponse]:
    with log.time(f"login_user: account={account} {{elapsed}}"):
        user = db.scalar(select(User).where(or_(User.email == account, User.phone == account)))
        if user is None or not verify_password(password, user.password_hash):
            return Result.failure(AuthErrors.INVALID_CREDENTIALS)
        if needs_password_upgrade(user.password_hash):
            user.password_hash = hash_password(password)
        if user.status != UserStatus.ACTIVE.value:
            return Result.failure(AuthErrors.USER_DISABLED)

        now = utcnow()
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token()
        family = uuid.uuid4().hex
        db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_secret(refresh_token),
                family=family,
                expires_at=now + timedelta(days=30),
                revoked_at=None,
                last_used_at=None,
                created_ip=None,
                user_agent=None,
                created_at=now,
            )
        )
        return Result.success(AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_to_schema(user),
        ))


def refresh_tokens(db: Session, *, refresh_token: str) -> Result[AuthTokenResponse]:
    with log.time("refresh_tokens {elapsed}"):
        token_hash = hash_secret(refresh_token)
        record = db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if record is None:
            return Result.failure(AuthErrors.INVALID_TOKEN)
        now = utcnow()
        if record.expires_at < now:
            return Result.failure(AuthErrors.TOKEN_EXPIRED)
        if record.revoked_at is not None:
            if record.family:
                db.execute(
                    update(RefreshToken)
                    .where(RefreshToken.family == record.family)
                    .values(revoked_at=now)
                )
            return Result.failure(AuthErrors.TOKEN_REUSE)
        record.revoked_at = now
        record.last_used_at = now
        db.flush()
        user = db.get(User, record.user_id)
        if user is None or user.status != UserStatus.ACTIVE.value:
            return Result.failure(AuthErrors.ACCOUNT_NOT_FOUND_OR_DISABLED)
        family = record.family or uuid.uuid4().hex
        new_access = create_access_token(user.id, user.role)
        new_refresh = create_refresh_token()
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)
        db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_secret(new_refresh),
                family=family,
                expires_at=expires_at,
                created_at=now,
            )
        )
        return Result.success(AuthTokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_to_schema(user),
        ))
