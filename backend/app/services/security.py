import hashlib
import hmac
import secrets


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_secret(value: str, digest: str) -> bool:
    return hmac.compare_digest(hash_secret(value), digest)


def make_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    # TODO(security): replace with passlib/argon2 before production.
    return hash_secret(password)


def verify_password(password: str, password_hash: str) -> bool:
    return verify_secret(password, password_hash)
