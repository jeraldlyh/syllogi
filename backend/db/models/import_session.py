import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel

from lib.mixin.serializer import SerializerMixin


class ImportProvider(enum.Enum):
    spotify = "spotify"
    youtube = "youtube"


class ImportSession(SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    provider: ImportProvider = Field(nullable=False, index=True)
    provider_playlist_id: str = Field(max_length=128, nullable=False, index=True)
    provider_playlist_name: str = Field(default="", max_length=512, nullable=False)

    target_user_id: str = Field(max_length=128, nullable=False, index=True)
    target_username: str = Field(default="", max_length=128, nullable=False)
    target_playlist_id: str = Field(max_length=128, nullable=False, index=True)
    target_playlist_name: str = Field(default="", max_length=512, nullable=False)

    total_tracks: int = Field(default=0, nullable=False)
    new_tracks: int = Field(default=0, nullable=False)
    outdated_tracks: int = Field(default=0, nullable=False)
    missing_tracks: int = Field(default=0, nullable=False)

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    finished_at: Optional[datetime] = Field(default=None, nullable=True)
    duration_seconds: int = Field(default=0, nullable=False)
    success: bool = Field(default=True, nullable=False)
    error_message: Optional[str] = Field(default=None, max_length=1024, nullable=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
