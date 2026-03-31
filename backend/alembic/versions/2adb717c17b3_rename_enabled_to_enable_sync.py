"""rename-enabled-to-enable-sync

Revision ID: 2adb717c17b3
Revises: 07c0ac966e87
Create Date: 2026-03-31 13:51:08.171254

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "2adb717c17b3"
down_revision: Union[str, Sequence[str], None] = "07c0ac966e87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("playlist", "enabled", new_column_name="enable_sync")


def downgrade() -> None:
    op.alter_column("playlist", "enable_sync", new_column_name="enabled")
