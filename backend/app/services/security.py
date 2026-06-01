import hashlib
import hmac
import secrets

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def _looks_like_raw_sha256(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_secret(value: str, digest: str) -> bool:
    return hmac.compare_digest(hash_secret(value), digest)


def make_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if _looks_like_raw_sha256(password_hash):
        legacy_ok = verify_secret(password, password_hash)
        return legacy_ok
    try:
        return pwd_context.verify(password, password_hash)
    except ValueError:
        return False


def needs_password_upgrade(password_hash: str) -> bool:
    return _looks_like_raw_sha256(password_hash)
