"""add-mixed-to-recommendationstrategy

Revision ID: 3156ac7e280d
Revises: 7bed13ea712a
Create Date: 2026-04-23 20:39:43.109000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3156ac7e280d"
down_revision: Union[str, Sequence[str], None] = "7bed13ea712a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE recommendationstrategy ADD VALUE IF NOT EXISTS 'mixed'")


def downgrade() -> None:
    """Downgrade schema."""
    # NOTE: Removal of enum value is not supported without recreating the type
    pass
