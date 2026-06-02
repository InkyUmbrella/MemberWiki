import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.error_codes import AuthErrors
from app.core.result import Result
from app.models.verification_code import VerificationCode
from app.services.security import hash_secret, verify_secret


def generate_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(6))


def persist_code(
    db: Session,
    *,
    channel: str,
    target: str,
    purpose: str,
    code: str,
    ip: str | None = None,
    ua: str | None = None,
) -> VerificationCode:
    now = datetime.now(timezone.utc)
    record = VerificationCode(
        channel=channel,
        target=target,
        purpose=purpose,
        code_hash=hash_secret(code),
        expires_at=now + timedelta(minutes=10),
        attempt_count=0,
        request_ip=ip,
        user_agent=ua,
        created_at=now,
    )
    db.add(record)
    return record


def verify_and_consume(
    db: Session,
    *,
    target: str,
    purpose: str,
    code: str,
) -> Result[VerificationCode]:
    from sqlalchemy import select

    now = datetime.now(timezone.utc)
    record = db.scalar(
        select(VerificationCode)
        .where(
            VerificationCode.target == target,
            VerificationCode.purpose == purpose,
            VerificationCode.consumed_at.is_(None),
        )
        .order_by(VerificationCode.created_at.desc())
        .limit(1)
    )
    if record is None:
        return Result.failure(AuthErrors.INVALID_CODE)
    if record.expires_at.replace(tzinfo=timezone.utc) < now:
        return Result.failure(AuthErrors.INVALID_CODE)
    record.attempt_count += 1
    if not verify_secret(code, record.code_hash):
        return Result.failure(AuthErrors.INVALID_CODE)
    record.consumed_at = now
    return Result.success(record)
