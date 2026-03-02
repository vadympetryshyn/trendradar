"""drop sentiment_score column

Revision ID: 6847b58f2d5b
Revises:
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa

revision = "6847b58f2d5b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='trends' AND column_name='sentiment_score'"
        )
    ).fetchone()
    if result:
        op.drop_column("trends", "sentiment_score")


def downgrade() -> None:
    op.add_column(
        "trends",
        sa.Column("sentiment_score", sa.Float(), nullable=True, server_default="0.0"),
    )
