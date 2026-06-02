from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.media_asset import MediaAsset
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import AwardItem, ExperienceItem
from app.services.auth_service import register_user
from app.services.upload_service import create_media_asset


def draft_payload() -> tuple[list[ExperienceItem], list[AwardItem]]:
    return (
        [
            ExperienceItem(
                title="Backend Lead",
                organization="MemberWiki",
                description="Built review workflow",
                start_date="2025-09-01",
                end_date=None,
            )
        ],
        [
            AwardItem(
                name="Innovation Prize",
                level="School",
                year=2025,
                description="Project owner",
            )
        ],
    )


def register_member(
    db: Session,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
    password: str = "Passw0rd!23",
) -> tuple[User, Profile]:
    result = register_user(db, name=name, email=email, phone=None, password=password)
    response = result.unwrap()
    db.commit()
    user = db.get(User, response.user.id)
    profile = db.query(Profile).filter(Profile.user_id == user.id).one()
    return user, profile


def register_admin(
    db: Session,
    *,
    name: str = "Admin",
    email: str = "admin@example.com",
) -> tuple[User, Profile]:
    user, profile = register_member(db, name=name, email=email)
    user.role = UserRole.ADMIN.value
    db.flush()
    return user, profile


def create_proof_asset(
    db: Session,
    *,
    owner_user_id: int,
    file_path: str = "proofs/proof.pdf",
    file_name: str = "proof.pdf",
) -> MediaAsset:
    return create_media_asset(
        db,
        owner_user_id=owner_user_id,
        file_name=file_name,
        file_path=file_path,
        file_type="application/pdf",
        file_size=128,
    ).unwrap()
