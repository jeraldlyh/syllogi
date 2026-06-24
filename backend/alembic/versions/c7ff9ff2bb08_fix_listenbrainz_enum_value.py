"""fix-add-listenbrainz-to-provider-enum

Revision ID: fix_listenbrainz_enum
Revises: c2d0973d5592
Create Date: 2026-06-24

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7ff9ff2bb08"
down_revision: Union[str, Sequence[str], None] = "c2d0973d5592"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE recommendationprovider ADD VALUE IF NOT EXISTS 'listenbrainz'"
    )


def downgrade() -> None:
    pass
