"""add-listenbrainz-username-and-recommendation-provider

Revision ID: c2d0973d5592
Revises: a347w9rzl2qk
Create Date: 2026-06-23 23:07:57.472079

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2d0973d5592"
down_revision: Union[str, Sequence[str], None] = "a347w9rzl2qk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "musicserveruser",
        sa.Column("listenbrainz_username", sa.String(length=128), nullable=True),
    )
    op.execute(
        "UPDATE musicserveruser SET listenbrainz_username = '' WHERE listenbrainz_username IS NULL"
    )
    op.alter_column(
        "musicserveruser",
        "listenbrainz_username",
        existing_type=sa.String(length=128),
        nullable=False,
    )

    op.add_column(
        "recommendation",
        sa.Column(
            "provider",
            sa.Enum("lastfm", "listenbrainz", name="recommendationprovider"),
            nullable=True,
        ),
    )
    op.execute("UPDATE recommendation SET provider = 'lastfm' WHERE provider IS NULL")
    op.alter_column(
        "recommendation",
        "provider",
        existing_type=sa.Enum("lastfm", "listenbrainz", name="recommendationprovider"),
        nullable=False,
    )
    op.create_index(
        op.f("ix_recommendation_provider"), "recommendation", ["provider"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_recommendation_provider"), table_name="recommendation")
    op.drop_column("recommendation", "provider")
    op.drop_column("musicserveruser", "listenbrainz_username")
