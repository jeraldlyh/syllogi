import enum
import uuid
import sqlalchemy as sa
from datetime import datetime
from typing import Any, cast

from sqlmodel import Field, Relationship, SQLModel

from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin
from lib.utils import get_now


class RecommendationStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class RecommendationTrackType(enum.Enum):
    total = "total"
    matched = "matched"
    missing = "missing"
    downloaded = "downloaded"


class RecommendationProvider(enum.Enum):
    lastfm = "lastfm"


class RecommendationStrategy(enum.Enum):
    top_tracks = "top_tracks"
    recent_tracks = "recent_tracks"


class RecommendationSetting(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    username: str = Field(max_length=128, nullable=False, unique=True, index=True)
    strategy: RecommendationStrategy = Field(nullable=False)
    lastfm_username: str = Field(max_length=128, nullable=False)
    requested_count: int = Field(default=50, nullable=False)


class RecommendationSession(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    username: str = Field(max_length=128, nullable=False, index=True)
    provider: RecommendationProvider = Field(nullable=False, index=True)

    strategy: RecommendationStrategy = Field(nullable=False)
    requested_count: int = Field(default=50, nullable=False)
    generated_count: int = Field(default=0, nullable=False)

    started_at: datetime = Field(
        default=get_now(),
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )
    finished_at: datetime = Field(
        default=get_now(),
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )
    duration_seconds: int = Field(default=0, nullable=False)

    status: RecommendationStatus = Field(nullable=False)
    tracks: list["RecommendationSessionTrack"] = Relationship(back_populates="session")

    error_message: str | None = Field(default=None, max_length=1024, nullable=True)


class RecommendationSessionTrack(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    recommendation_session_id: uuid.UUID = Field(
        foreign_key="recommendationsession.id", nullable=False, index=True
    )
    session: RecommendationSession = Relationship(back_populates="tracks")

    name: str = Field(max_length=256, nullable=False)
    type: RecommendationTrackType = Field(nullable=False)
