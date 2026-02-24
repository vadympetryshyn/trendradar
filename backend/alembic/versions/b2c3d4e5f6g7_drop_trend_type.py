"""drop trend_type column

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("trends", "trend_type")


def downgrade() -> None:
    op.add_column(
        "trends",
        sa.Column("trend_type", sa.String(20), nullable=False, server_default="trend"),
    )
