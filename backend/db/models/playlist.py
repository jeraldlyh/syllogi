import enum
import uuid

from sqlmodel import Field, SQLModel

from lib.utils import _format_time_with_locale
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
    enable_sync: bool = Field(default=True, nullable=False)
    enable_download: bool = Field(default=True, nullable=False)
    cron_expression: str = Field(default="", max_length=128, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "provider": self.provider.value,
            "playlist_id": self.playlist_id,
            "playlist_name": self.playlist_name,
            "username": self.username,
            "enable_sync": self.enable_sync,
            "enable_download": self.enable_download,
            "cron_expression": self.cron_expression,
            "created_at": _format_time_with_locale(self.created_at),
            "updated_at": _format_time_with_locale(self.updated_at),
        }
