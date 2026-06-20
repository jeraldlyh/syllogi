"""drop-lastfm-username-from-recommendation-and-migrate-blend-users

Revision ID: a347w9rzl2qk
Revises: 5xuo84yj9j0h
Create Date: 2026-06-20 12:00:00.000000

"""

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "a347w9rzl2qk"
down_revision: Union[str, Sequence[str], None] = "5xuo84yj9j0h"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _migrate_blend_users(table: str) -> None:
    """Transform blend_users from [{name, lastfm_username}, ...] to [name, ...]."""
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(f"SELECT id, blend_users FROM {table} WHERE blend_users IS NOT NULL")
    ).fetchall()

    for row in rows:
        row_id, raw = row
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(data, list) or not data:
            continue

        if isinstance(data[0], dict):
            new_data = [entry.get("name", "") for entry in data]
            bind.execute(
                sa.text(
                    f"UPDATE {table} SET blend_users = :blend_users WHERE id = :id"
                ),
                {"blend_users": json.dumps(new_data), "id": row_id},
            )


def upgrade() -> None:
    """Upgrade schema."""
    _migrate_blend_users("recommendation")
    _migrate_blend_users("recommendationsession")

    op.drop_column("recommendation", "lastfm_username")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "recommendation",
        sa.Column(
            "lastfm_username",
            sqlmodel.sql.sqltypes.AutoString(length=128),
            nullable=True,
            server_default="",
        ),
    )
