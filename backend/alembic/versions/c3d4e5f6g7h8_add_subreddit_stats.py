"""add subreddit_stats table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-25

"""
from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa

revision = "c3d4e5f6g7h8"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "subreddit_stats" not in insp.get_table_names():
        op.create_table(
            "subreddit_stats",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("subreddit", sa.String(100), nullable=False),
            sa.Column("avg_score", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("avg_comments", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("avg_age_hours", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("avg_velocity", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("post_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = {idx["name"] for idx in insp.get_indexes("subreddit_stats")}
    if "ix_subreddit_stats_subreddit" not in indexes:
        op.create_index("ix_subreddit_stats_subreddit", "subreddit_stats", ["subreddit"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_subreddit_stats_subreddit", table_name="subreddit_stats")
    op.drop_table("subreddit_stats")
