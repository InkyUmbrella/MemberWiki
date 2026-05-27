"""Expand MemberWiki schema v1.1.

Revision ID: 202605260001
Revises: 08f4723ba902
Create Date: 2026-05-26 00:01:00.000000

This migration is additive and keeps V1 table names, primary keys and core
foreign keys. SQLite cannot alter existing CHECK/NULL constraints in place, so
the users.email nullable compatibility change is intentionally not applied.
TODO(product): if pure phone registration is accepted, rebuild users with
email nullable and CHECK(email IS NOT NULL OR phone IS NOT NULL).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202605260001"
down_revision: Union[str, None] = "08f4723ba902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        if not _has_column("users", "avatar_url"):
            batch_op.add_column(sa.Column("avatar_url", sa.Text(), nullable=True))
    op.create_index("ix_users_display_name", "users", ["display_name"], unique=False)
    op.create_index("ix_users_role_status", "users", ["role", "status"], unique=False)

    if not _has_table("verification_codes"):
        op.create_table(
            "verification_codes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("channel", sa.Text(), nullable=False),
            sa.Column("target", sa.Text(), nullable=False),
            sa.Column("purpose", sa.Text(), nullable=False),
            sa.Column("code_hash", sa.Text(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("consumed_at", sa.DateTime(), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("request_ip", sa.Text(), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint("channel IN ('email', 'sms')", name="ck_verification_codes_channel"),
            sa.CheckConstraint(
                "purpose IN ('register', 'login', 'reset_password')",
                name="ck_verification_codes_purpose",
            ),
        )
    op.create_index("ix_verification_codes_expires_at", "verification_codes", ["expires_at"], unique=False)
    op.create_index(
        "ix_verification_codes_target_purpose_created_at",
        "verification_codes",
        ["target", "purpose", "created_at"],
        unique=False,
    )

    if not _has_table("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.Text(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column("created_ip", sa.Text(), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        )
    op.create_index("ix_refresh_tokens_user_expires_at", "refresh_tokens", ["user_id", "expires_at"], unique=False)

    with op.batch_alter_table("profiles") as batch_op:
        if not _has_column("profiles", "published_version_no"):
            batch_op.add_column(sa.Column("published_version_no", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_profiles_updated_at", "profiles", ["updated_at"], unique=False)
    op.create_index("ix_profiles_visibility_updated_at", "profiles", ["visibility", "updated_at"], unique=False)

    with op.batch_alter_table("profile_drafts") as batch_op:
        if not _has_column("profile_drafts", "review_status"):
            batch_op.add_column(sa.Column("review_status", sa.Text(), nullable=False, server_default="draft"))
        if not _has_column("profile_drafts", "updated_at"):
            # Data copy compatibility: old rows use created_at as initial updated_at.
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE profile_drafts SET updated_at = created_at WHERE updated_at IS NULL")
    with op.batch_alter_table("profile_drafts", recreate="always") as batch_op:
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.create_check_constraint(
            "ck_profile_drafts_review_status",
            "review_status IN ('draft', 'pending', 'approved', 'rejected')",
        )
    op.create_index(
        "uq_profile_drafts_profile_version",
        "profile_drafts",
        ["profile_id", "version_no"],
        unique=True,
    )
    op.create_index("ix_profile_drafts_editor_latest", "profile_drafts", ["editor_user_id", "is_latest"], unique=False)
    op.create_index(
        "uq_profile_drafts_one_latest",
        "profile_drafts",
        ["profile_id"],
        unique=True,
        sqlite_where=sa.text("is_latest = 1"),
    )

    with op.batch_alter_table("review_requests") as batch_op:
        if not _has_column("review_requests", "draft_id"):
            batch_op.add_column(
                sa.Column(
                    "draft_id",
                    sa.Integer(),
                    nullable=True,
                )
            )
        if not _has_column("review_requests", "reject_reason"):
            batch_op.add_column(sa.Column("reject_reason", sa.Text(), nullable=True))
        if not _has_column("review_requests", "updated_at"):
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE review_requests SET updated_at = COALESCE(reviewed_at, submitted_at) WHERE updated_at IS NULL")
    with op.batch_alter_table("review_requests", recreate="always") as batch_op:
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.create_foreign_key(
            "fk_review_requests_draft_id_profile_drafts",
            "profile_drafts",
            ["draft_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_review_requests_reviewer_status", "review_requests", ["reviewer_user_id", "status"], unique=False)
    op.create_index(
        "uq_review_requests_one_pending",
        "review_requests",
        ["profile_id"],
        unique=True,
        sqlite_where=sa.text("status = 'pending'"),
    )

    with op.batch_alter_table("achievements") as batch_op:
        for column in [
            sa.Column("organization", sa.Text(), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("award_level", sa.Text(), nullable=True),
            sa.Column("award_year", sa.Integer(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        ]:
            if not _has_column("achievements", column.name):
                batch_op.add_column(column)
    op.execute("UPDATE achievements SET updated_at = created_at WHERE updated_at IS NULL")
    with op.batch_alter_table("achievements", recreate="always") as batch_op:
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.create_check_constraint(
            "ck_achievements_award_year",
            "award_year IS NULL OR (award_year >= 1900 AND award_year <= 2100)",
        )
    op.create_index("ix_achievements_title", "achievements", ["title"], unique=False)
    op.create_index("ix_achievements_profile_category", "achievements", ["profile_id", "category"], unique=False)
    op.create_index(
        "ix_achievements_award_keyword",
        "achievements",
        ["category", "title", "award_level"],
        unique=False,
    )

    with op.batch_alter_table("media_assets") as batch_op:
        if not _has_column("media_assets", "file_name"):
            batch_op.add_column(sa.Column("file_name", sa.Text(), nullable=True))
        if not _has_column("media_assets", "checksum_sha256"):
            batch_op.add_column(sa.Column("checksum_sha256", sa.Text(), nullable=True))
        if not _has_column("media_assets", "deleted_at"):
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE media_assets SET file_name = file_path WHERE file_name IS NULL")
    with op.batch_alter_table("media_assets", recreate="always") as batch_op:
        batch_op.alter_column("file_name", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("ref_type", existing_type=sa.Text(), nullable=True)
        batch_op.alter_column("ref_id", existing_type=sa.Integer(), nullable=True)
        batch_op.create_check_constraint(
            "ck_media_assets_file_size_positive",
            "file_size > 0",
        )
    op.create_index("uq_media_assets_file_path", "media_assets", ["file_path"], unique=True)
    op.create_index("ix_media_assets_deleted_at", "media_assets", ["deleted_at"], unique=False)
    op.create_index("ix_media_assets_owner_created_at", "media_assets", ["owner_user_id", "created_at"], unique=False)

    if not _has_table("profile_draft_files"):
        op.create_table(
            "profile_draft_files",
            sa.Column("draft_id", sa.Integer(), sa.ForeignKey("profile_drafts.id", ondelete="CASCADE"), nullable=False),
            sa.Column(
                "media_asset_id",
                sa.Integer(),
                sa.ForeignKey("media_assets.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("draft_id", "media_asset_id", name="pk_profile_draft_files"),
        )
    op.create_index(
        "ix_profile_draft_files_media_asset_id",
        "profile_draft_files",
        ["media_asset_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_profile_draft_files_media_asset_id", table_name="profile_draft_files")
    op.drop_table("profile_draft_files")

    op.drop_index("ix_media_assets_owner_created_at", table_name="media_assets")
    op.drop_index("ix_media_assets_deleted_at", table_name="media_assets")
    op.drop_index("uq_media_assets_file_path", table_name="media_assets")
    op.create_table(
        "_media_assets_v1",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("ref_type", sa.Text(), nullable=False),
        sa.Column("ref_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.Text(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("ref_type IN ('profile', 'review')", name="ck_media_assets_ref_type"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.execute(
        """
        INSERT INTO _media_assets_v1
            (id, owner_user_id, ref_type, ref_id, file_path, file_type, file_size, created_at)
        SELECT
            id, owner_user_id, COALESCE(ref_type, 'profile'), COALESCE(ref_id, 0),
            file_path, file_type, file_size, created_at
        FROM media_assets
        """
    )
    op.drop_table("media_assets")
    op.rename_table("_media_assets_v1", "media_assets")

    op.drop_index("ix_achievements_award_keyword", table_name="achievements")
    op.drop_index("ix_achievements_profile_category", table_name="achievements")
    op.drop_index("ix_achievements_title", table_name="achievements")
    op.create_table(
        "_achievements_v1",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("happened_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("category IN ('award', 'experience')", name="ck_achievements_category"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.execute(
        """
        INSERT INTO _achievements_v1
            (id, profile_id, category, title, description, happened_at, created_at)
        SELECT id, profile_id, category, title, description, happened_at, created_at
        FROM achievements
        """
    )
    op.drop_table("achievements")
    op.rename_table("_achievements_v1", "achievements")

    op.drop_index("uq_review_requests_one_pending", table_name="review_requests")
    op.drop_index("ix_review_requests_reviewer_status", table_name="review_requests")
    op.create_table(
        "_review_requests_v1",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("submitter_user_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("change_payload", sa.Text(), nullable=False),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_review_requests_status"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitter_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.execute(
        """
        INSERT INTO _review_requests_v1
            (id, profile_id, submitter_user_id, reviewer_user_id, status,
             change_payload, review_comment, submitted_at, reviewed_at)
        SELECT id, profile_id, submitter_user_id, reviewer_user_id, status,
               change_payload, review_comment, submitted_at, reviewed_at
        FROM review_requests
        """
    )
    op.drop_table("review_requests")
    op.rename_table("_review_requests_v1", "review_requests")

    op.drop_index("uq_profile_drafts_one_latest", table_name="profile_drafts")
    op.drop_index("ix_profile_drafts_editor_latest", table_name="profile_drafts")
    op.drop_index("uq_profile_drafts_profile_version", table_name="profile_drafts")
    op.create_table(
        "_profile_drafts_v1",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("editor_user_id", sa.Integer(), nullable=False),
        sa.Column("draft_content", sa.Text(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["editor_user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.execute(
        """
        INSERT INTO _profile_drafts_v1
            (id, profile_id, editor_user_id, draft_content, version_no, is_latest, created_at)
        SELECT id, profile_id, editor_user_id, draft_content, version_no, is_latest, created_at
        FROM profile_drafts
        """
    )
    op.drop_table("profile_drafts")
    op.rename_table("_profile_drafts_v1", "profile_drafts")

    op.drop_index("ix_profiles_visibility_updated_at", table_name="profiles")
    op.drop_index("ix_profiles_updated_at", table_name="profiles")
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_column("published_version_no")

    op.create_index(
        "ix_review_requests_status_submitted_at",
        "review_requests",
        ["status", "submitted_at"],
        unique=False,
    )
    op.create_index(
        "ix_achievements_profile_id_happened_at",
        "achievements",
        ["profile_id", "happened_at"],
        unique=False,
    )

    op.drop_index("ix_refresh_tokens_user_expires_at", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_verification_codes_target_purpose_created_at", table_name="verification_codes")
    op.drop_index("ix_verification_codes_expires_at", table_name="verification_codes")
    op.drop_table("verification_codes")

    op.drop_index("ix_users_role_status", table_name="users")
    op.drop_index("ix_users_display_name", table_name="users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("avatar_url")
