import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import login_user, refresh_tokens
from app.services.security import (
    create_access_token,
    decode_access_token,
    needs_password_upgrade,
    verify_password,
)
from tests.helpers.factories import register_member


def test_register_login_persistence(db: Session) -> None:
    user, _ = register_member(db)

    assert db.get(User, user.id).display_name == "Alice"
    assert db.query(RefreshToken).filter(RefreshToken.user_id == user.id).count() == 1

    result = login_user(db, account="alice@example.com", password="Passw0rd!23")
    assert result.ok
    response = result.unwrap()
    db.commit()

    assert response.user.id == user.id
    assert db.query(RefreshToken).filter(RefreshToken.user_id == user.id).count() == 2


def test_login_rejects_wrong_password(db: Session) -> None:
    register_member(db)

    result = login_user(db, account="alice@example.com", password="WrongPass123")
    assert not result.ok
    assert result.code == "UNAUTHORIZED"


def test_access_token_is_jwt_with_claims(db: Session) -> None:
    user, _ = register_member(db)
    token = create_access_token(user.id, user.role)
    payload = decode_access_token(token)

    assert int(payload["sub"]) == user.id
    assert payload["role"] == user.role
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "jti" in payload


def test_decode_invalid_token_fails(db: Session) -> None:
    with pytest.raises(Exception):
        decode_access_token("not-a-valid-token")


def test_password_upgrade_on_login(db: Session) -> None:
    from app.services.security import hash_secret

    register_member(db, name="Legacy", email="legacy@example.com")
    db.commit()
    user = db.scalar(select(User).where(User.email == "legacy@example.com"))
    assert user is not None
    user.password_hash = hash_secret("OldPass123")
    db.commit()

    assert needs_password_upgrade(user.password_hash)

    result = login_user(db, account="legacy@example.com", password="OldPass123")
    assert result.ok
    db.commit()

    user = db.get(User, user.id)
    assert user is not None
    assert not needs_password_upgrade(user.password_hash)
    assert verify_password("OldPass123", user.password_hash)


def test_refresh_token_rotation(db: Session) -> None:
    register_member(db, name="Bob", email="bob@example.com")
    login_result = login_user(db, account="bob@example.com", password="Passw0rd!23")
    assert login_result.ok
    response = login_result.unwrap()
    db.commit()

    old_refresh = response.refresh_token
    token_count_before = db.query(RefreshToken).filter(
        RefreshToken.user_id == response.user.id,
        RefreshToken.revoked_at.is_(None),
    ).count()

    refresh_result = refresh_tokens(db, refresh_token=old_refresh)
    assert refresh_result.ok
    new_response = refresh_result.unwrap()
    db.commit()

    assert new_response.access_token != response.access_token
    assert new_response.refresh_token != old_refresh

    token_count_after = db.query(RefreshToken).filter(
        RefreshToken.user_id == response.user.id,
        RefreshToken.revoked_at.is_(None),
    ).count()
    assert token_count_after == token_count_before


def test_refresh_reuse_detected(db: Session) -> None:
    register_member(db, name="Eve", email="eve@example.com")
    login_result = login_user(db, account="eve@example.com", password="Passw0rd!23")
    assert login_result.ok
    response = login_result.unwrap()
    db.commit()

    refresh_tokens(db, refresh_token=response.refresh_token)
    db.commit()

    result = refresh_tokens(db, refresh_token=response.refresh_token)
    assert not result.ok
    assert "token reuse" in (result.error or "").lower()
