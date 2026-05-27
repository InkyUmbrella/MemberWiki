from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReviewRequest(Base):
    __tablename__ = "review_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_review_requests_status",
        ),
        Index("ix_review_requests_status_submitted_at", "status", "submitted_at"),
        Index("ix_review_requests_reviewer_status", "reviewer_user_id", "status"),
        # SQLite partial unique index: only one pending review may exist per profile.
        Index(
            "uq_review_requests_one_pending",
            "profile_id",
            unique=True,
            sqlite_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("profile_drafts.id", ondelete="SET NULL"), nullable=True)
    submitter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewer_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    change_payload: Mapped[str] = mapped_column(Text, nullable=False)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
