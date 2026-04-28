"""rename-kind-to-type

Revision ID: d09e406a2f04
Revises: 429a26cd4a74
Create Date: 2026-04-19 20:11:42.942637

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d09e406a2f04"
down_revision: Union[str, Sequence[str], None] = "429a26cd4a74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tracklistkind RENAME TO syncsessiontracktype")
    op.alter_column("syncsessiontrack", "kind", new_column_name="type")
    op.execute(
        "ALTER INDEX ix_syncsessiontrack_kind RENAME TO ix_syncsessiontrack_type"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER INDEX ix_syncsessiontrack_type RENAME TO ix_syncsessiontrack_kind"
    )
    op.alter_column("syncsessiontrack", "type", new_column_name="kind")
    op.execute("ALTER TYPE syncsessiontracktype RENAME TO tracklistkind")
