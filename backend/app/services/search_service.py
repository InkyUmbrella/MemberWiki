from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.log import get_logger
from app.core.result import Result
from app.models.achievement import Achievement
from app.models.enums import AchievementCategory
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import SearchResultItem

log = get_logger(__name__)


def search_members(db: Session, *, keyword: str | None = None, limit: int = 20) -> Result[tuple[list[SearchResultItem], int]]:
    with log.time(f"search_members: keyword={keyword} {{elapsed}}"):
        award_counts = (
            select(Achievement.profile_id, func.count(Achievement.id).label("award_count"))
            .where(Achievement.category == AchievementCategory.AWARD.value)
            .group_by(Achievement.profile_id)
            .subquery()
        )
        base = (
            select(Profile, User, func.coalesce(award_counts.c.award_count, 0))
            .join(User, User.id == Profile.user_id)
            .outerjoin(award_counts, award_counts.c.profile_id == Profile.id)
            .where(Profile.visibility == "public")
        )
        if keyword:
            like = f"%{keyword}%"
            base = base.where((Profile.bio.like(like)) | (User.display_name.like(like)))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = db.scalar(count_stmt) or 0

        rows = db.execute(base.order_by(Profile.updated_at.desc()).limit(limit)).all()
        results: list[SearchResultItem] = []
        for profile, user, award_count in rows:
            results.append(
                SearchResultItem(
                    profile_id=profile.id,
                    user_name=user.display_name,
                    bio_highlight=profile.bio or "",
                    award_count=award_count,
                    updated_at=profile.updated_at,
                )
            )
        return Result.success((results, total))
