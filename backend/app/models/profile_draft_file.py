from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfileDraftFile(Base):
    __tablename__ = "profile_draft_files"
    __table_args__ = (
        PrimaryKeyConstraint("draft_id", "media_asset_id", name="pk_profile_draft_files"),
        Index("ix_profile_draft_files_media_asset_id", "media_asset_id"),
    )

    draft_id: Mapped[int] = mapped_column(
        ForeignKey("profile_drafts.id", ondelete="CASCADE"),
        nullable=False,
    )
    media_asset_id: Mapped[int] = mapped_column(
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
