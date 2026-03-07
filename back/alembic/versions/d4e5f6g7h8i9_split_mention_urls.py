"""split mention_urls from source_urls

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trends",
        sa.Column("mention_urls", ARRAY(sa.String()), server_default="{}", nullable=False),
    )

    # Migrate existing data: move Reddit URLs to mention_urls, keep non-Reddit in source_urls
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE trends
        SET mention_urls = (
            SELECT COALESCE(array_agg(u), '{}')
            FROM unnest(source_urls) AS u
            WHERE u LIKE '%reddit.com%'
        ),
        source_urls = (
            SELECT COALESCE(array_agg(u), '{}')
            FROM unnest(source_urls) AS u
            WHERE u NOT LIKE '%reddit.com%'
        )
        WHERE array_length(source_urls, 1) IS NOT NULL
    """))


def downgrade() -> None:
    # Merge mention_urls back into source_urls
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE trends
        SET source_urls = source_urls || mention_urls
        WHERE array_length(mention_urls, 1) IS NOT NULL
    """))

    op.drop_column("trends", "mention_urls")
