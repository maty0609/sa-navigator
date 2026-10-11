"""add soft-delete columns to opportunities

Revision ID: 0002_opportunity_soft_delete
Revises: 0001_initial_schema
Create Date: 2026-10-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # type: ignore


# revision identifiers, used by Alembic.
revision: str = "0002_opportunity_soft_delete"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # deleted_at carries visibility; status stays business state. Keeping them
    # separate is what stops "deleted" and "lost the deal" colliding - see
    # AGENTS.md. Both nullable, so existing rows stay visible and unchanged.
    op.add_column(
        "opportunities",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Previous status, held so a restore is lossless instead of guessing "Lost".
    op.add_column(
        "opportunities",
        sa.Column("status_before_delete", sqlmodel.String(30), nullable=True),
    )
    # Partial index: every list/count query filters deleted_at IS NULL. The
    # predicate must be plain SQL - parameterized predicates are not allowed.
    op.create_index(
        "ix_opportunities_deleted_at",
        "opportunities",
        ["id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_opportunities_deleted_at", table_name="opportunities")
    op.drop_column("opportunities", "status_before_delete")
    op.drop_column("opportunities", "deleted_at")
