"""add-existed-to-download-session-status

Revision ID: 7e79d4942139
Revises: c7ff9ff2bb08
Create Date: 2026-06-28

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e79d4942139"
down_revision: Union[str, Sequence[str], None] = "c7ff9ff2bb08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE downloadsessionstatus ADD VALUE IF NOT EXISTS 'existed'")


def downgrade() -> None:
    pass
