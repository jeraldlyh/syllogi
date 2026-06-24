import enum
import uuid

import sqlalchemy as sa

from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin
from sqlmodel import Field, SQLModel


class MusicServerProvider(str, enum.Enum):
    jellyfin = "jellyfin"
    navidrome = "navidrome"


class MusicServerUser(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    username: str = Field(max_length=128, nullable=False, index=True)
    provider: MusicServerProvider = Field(nullable=False, index=True)
    password: str = Field(default="", max_length=256, nullable=False)
    lastfm_username: str = Field(default="", max_length=128, nullable=False)
    listenbrainz_username: str = Field(default="", max_length=128, nullable=False)

    __table_args__ = (
        sa.UniqueConstraint(
            "username", "provider", name="unique_musicserveruser_username_provider"
        ),
    )
