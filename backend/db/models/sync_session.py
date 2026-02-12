import enum
import uuid
import sqlalchemy as sa
from datetime import datetime
from typing import Any, Optional, cast

from sqlmodel import Field, Relationship, SQLModel

from lib.utils import _get_now
from lib.mixin.serializer import SerializerMixin
from lib.mixin.metadata import TimestampsMixin


class SyncProvider(enum.Enum):
    spotify = "spotify"
    youtube = "youtube"


class TrackListKind(enum.Enum):
    total = "total"
    new = "new"
    outdated = "outdated"
    missing = "missing"


class SyncSession(TimestampsMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    provider: SyncProvider = Field(nullable=False, index=True)
    provider_playlist_id: str = Field(max_length=128, nullable=False, index=True)
    provider_playlist_name: str = Field(default="", max_length=512, nullable=False)

    target_user_id: str = Field(max_length=128, nullable=False, index=True)
    target_username: str = Field(default="", max_length=128, nullable=False)
    target_playlist_id: str = Field(max_length=128, nullable=False, index=True)
    target_playlist_name: str = Field(default="", max_length=512, nullable=False)

    tracks: list["SyncSessionTrack"] = Relationship(back_populates="session")

    started_at: datetime = Field(
        default=_get_now(),
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )
    finished_at: datetime = Field(
        default=_get_now(),
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )
    duration_seconds: int = Field(default=0, nullable=False)
    success: bool = Field(default=True, nullable=False)
    error_message: Optional[str] = Field(default=None, max_length=1024, nullable=True)


class SyncSessionTrack(TimestampsMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    sync_session_id: uuid.UUID = Field(
        foreign_key="syncsession.id", index=True, nullable=False
    )
    kind: TrackListKind = Field(nullable=False, index=True)
    name: str = Field(max_length=512, nullable=False)

    session: SyncSession = Relationship(back_populates="tracks")
