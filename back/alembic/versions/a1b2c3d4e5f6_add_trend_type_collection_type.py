"""add trend_type and collection_type

Revision ID: a1b2c3d4e5f6
Revises: 6847b58f2d5b
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "6847b58f2d5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- trends table --
    op.add_column(
        "trends",
        sa.Column("trend_type", sa.String(20), nullable=False, server_default="trend"),
    )
    op.add_column(
        "trends",
        sa.Column("collection_type", sa.String(20), nullable=False, server_default="now"),
    )
    op.create_index(
        "ix_trends_niche_collection_status",
        "trends",
        ["niche_id", "collection_type", "status"],
    )

    # -- schedule_configs table --
    op.add_column(
        "schedule_configs",
        sa.Column("collection_type", sa.String(20), nullable=False, server_default="now"),
    )
    op.create_unique_constraint(
        "uq_schedule_niche_collection",
        "schedule_configs",
        ["niche_id", "collection_type"],
    )

    # -- collection_tasks table --
    op.add_column(
        "collection_tasks",
        sa.Column("collection_type", sa.String(20), nullable=False, server_default="now"),
    )

    # -- Data migration: create daily/weekly schedule configs for existing niches --
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT DISTINCT niche_id FROM schedule_configs")).fetchall()
    for (niche_id,) in rows:
        for ctype, interval in [("daily", 1440), ("weekly", 1440)]:
            exists = conn.execute(
                sa.text(
                    "SELECT 1 FROM schedule_configs WHERE niche_id = :nid AND collection_type = :ct"
                ),
                {"nid": niche_id, "ct": ctype},
            ).fetchone()
            if not exists:
                conn.execute(
                    sa.text(
                        "INSERT INTO schedule_configs (niche_id, collection_type, interval_minutes, is_enabled, updated_at) "
                        "VALUES (:nid, :ct, :interval, false, NOW())"
                    ),
                    {"nid": niche_id, "ct": ctype, "interval": interval},
                )


def downgrade() -> None:
    # -- collection_tasks --
    op.drop_column("collection_tasks", "collection_type")

    # -- schedule_configs: remove daily/weekly rows, then drop column --
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM schedule_configs WHERE collection_type != 'now'"))
    op.drop_constraint("uq_schedule_niche_collection", "schedule_configs", type_="unique")
    op.drop_column("schedule_configs", "collection_type")

    # -- trends --
    op.drop_index("ix_trends_niche_collection_status", table_name="trends")
    op.drop_column("trends", "collection_type")
    op.drop_column("trends", "trend_type")
