import pytest
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import login_user
from app.services.errors import UnauthorizedError
from tests.helpers.factories import register_member


def test_register_login_persistence(db: Session) -> None:
    user, _ = register_member(db)

    assert db.get(User, user.id).display_name == "Alice"
    assert db.query(RefreshToken).filter(RefreshToken.user_id == user.id).count() == 1

    response = login_user(db, account="alice@example.com", password="Passw0rd!23")
    db.commit()

    assert response.user.id == user.id
    assert db.query(RefreshToken).filter(RefreshToken.user_id == user.id).count() == 2


def test_login_rejects_wrong_password(db: Session) -> None:
    register_member(db)

    with pytest.raises(UnauthorizedError):
        login_user(db, account="alice@example.com", password="WrongPass123")
