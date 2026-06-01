"""Add family column to refresh_tokens for token rotation tracking.

Revision ID: 202606010001
Revises: 202605260001
Create Date: 2026-06-01 00:01:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202606010001"
down_revision: Union[str, None] = "202605260001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        if not _has_column("refresh_tokens", "family"):
            batch_op.add_column(sa.Column("family", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        if _has_column("refresh_tokens", "family"):
            batch_op.drop_column("family")
