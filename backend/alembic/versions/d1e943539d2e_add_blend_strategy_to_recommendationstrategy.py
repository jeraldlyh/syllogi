"""add-blend-strategy-to-recommendationstrategy

Revision ID: d1e943539d2e
Revises: a2dfc8f0e0e3
Create Date: 2026-06-14 21:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e943539d2e"
down_revision: str | Sequence[str] | None = "a2dfc8f0e0e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE recommendationstrategy ADD VALUE IF NOT EXISTS 'blend'")


def downgrade() -> None:
    """Downgrade schema."""
