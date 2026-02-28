import enum
import uuid

from sqlmodel import Field, SQLModel

from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin


class PlaylistProvider(enum.Enum):
    spotify = "spotify"
    youtube = "youtube"


class Playlist(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    provider: PlaylistProvider = Field(nullable=False, index=True)

    playlist_id: str = Field(max_length=128, nullable=False, index=True)
    playlist_name: str = Field(default="", max_length=512, nullable=False)

    username: str = Field(default="", max_length=128, nullable=False, index=True)
    enabled: bool = Field(default=True, nullable=False)
    cron_expression: str = Field(default="", max_length=128, nullable=False)
