from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfileDraft(Base):
    __tablename__ = "profile_drafts"
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('draft', 'pending', 'approved', 'rejected')",
            name="ck_profile_drafts_review_status",
        ),
        UniqueConstraint("profile_id", "version_no", name="uq_profile_drafts_profile_version"),
        Index("ix_profile_drafts_editor_latest", "editor_user_id", "is_latest"),
        # SQLite supports partial unique indexes. This keeps one latest draft per
        # profile without mutating historical draft rows beyond is_latest flips.
        Index(
            "uq_profile_drafts_one_latest",
            "profile_id",
            unique=True,
            sqlite_where=text("is_latest = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    editor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    draft_content: Mapped[str] = mapped_column(Text, nullable=False)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
