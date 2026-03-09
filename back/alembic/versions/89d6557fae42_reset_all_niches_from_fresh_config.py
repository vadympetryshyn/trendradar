"""reset_all_niches_from_fresh_config

Revision ID: 89d6557fae42
Revises: f6g7h8i9j0k1
Create Date: 2026-03-09 18:07:26.456244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89d6557fae42'
down_revision: Union[str, Sequence[str], None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Truncate niches and all dependent tables via CASCADE
    conn.execute(sa.text("TRUNCATE TABLE niches CASCADE"))


def downgrade() -> None:
    # No way to restore deleted data; seed_data() will repopulate on app start
    pass
