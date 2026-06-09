"""rename-playlist-to-sync

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-06-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "b1e2f3a4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.rename_table("playlist", "sync")

    op.execute("ALTER INDEX ix_playlist_playlist_id RENAME TO ix_sync_playlist_id")
    op.execute("ALTER INDEX ix_playlist_provider RENAME TO ix_sync_provider")
    op.execute("ALTER INDEX ix_playlist_username RENAME TO ix_sync_username")

    op.execute(
        "ALTER TABLE sync ALTER COLUMN provider TYPE syncprovider"
        " USING provider::text::syncprovider"
    )
    op.execute("DROP TYPE playlistprovider")


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("CREATE TYPE playlistprovider AS ENUM ('spotify', 'youtube')")

    op.execute(
        "ALTER TABLE sync ALTER COLUMN provider TYPE playlistprovider"
        " USING provider::text::playlistprovider"
    )

    op.execute("ALTER INDEX ix_sync_playlist_id RENAME TO ix_playlist_playlist_id")
    op.execute("ALTER INDEX ix_sync_provider RENAME TO ix_playlist_provider")
    op.execute("ALTER INDEX ix_sync_username RENAME TO ix_playlist_username")

    op.rename_table("sync", "playlist")
