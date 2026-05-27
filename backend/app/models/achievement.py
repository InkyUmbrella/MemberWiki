from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (
        CheckConstraint("category IN ('award', 'experience')", name="ck_achievements_category"),
        CheckConstraint(
            "award_year IS NULL OR (award_year >= 1900 AND award_year <= 2100)",
            name="ck_achievements_award_year",
        ),
        Index("ix_achievements_title", "title"),
        Index("ix_achievements_profile_category", "profile_id", "category"),
        Index("ix_achievements_profile_id_happened_at", "profile_id", "happened_at"),
        Index("ix_achievements_award_keyword", "category", "title", "award_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    award_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    award_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    happened_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
