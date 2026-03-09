"""update daily and weekly default intervals

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-03-09

"""
from alembic import op
import sqlalchemy as sa

revision = "f6g7h8i9j0k1"
down_revision = "e5f6g7h8i9j0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE schedule_configs
        SET interval_minutes = 360
        WHERE collection_type = 'daily'
    """))
    conn.execute(sa.text("""
        UPDATE schedule_configs
        SET interval_minutes = 1440
        WHERE collection_type = 'weekly'
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE schedule_configs
        SET interval_minutes = 60
        WHERE collection_type = 'daily'
    """))
    conn.execute(sa.text("""
        UPDATE schedule_configs
        SET interval_minutes = 1440
        WHERE collection_type = 'weekly'
    """))
