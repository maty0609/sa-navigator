"""add soft-delete columns to opportunities

Revision ID: 0002_opportunity_soft_delete
Revises: 0001_initial_schema
Create Date: 2026-10-11

`deleted_at` carries visibility and `status` stays business state. Keeping them
in separate columns is what stops "this record was deleted" and "we lost the
deal" from colliding - see AGENTS.md. Both are nullable, so existing rows are
unaffected and stay visible.

`status_before_delete` holds the previous status so a restore is lossless rather
than a guess at "Lost".

The partial index backs the predicate every list/count query now carries. It must
be plain SQL: PostgreSQL cannot use a parameterized predicate for a partial
index.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = "0002_opportunity_soft_delete"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "opportunities",
        sa.Column("deleted_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column(
            "status_before_delete",
            sqlmodel.sql.sqltypes.AutoString(length=30),
            nullable=True,
        ),
    )
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
