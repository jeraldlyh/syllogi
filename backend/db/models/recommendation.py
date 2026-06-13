import enum
import uuid
import sqlalchemy as sa
from datetime import datetime
from typing import Any, cast

from sqlmodel import Field, Relationship, SQLModel

from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin
from lib.models.blend import BlendUser
from lib.utils import format_time_with_locale, get_now


class RecommendationStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class RecommendationTrackType(str, enum.Enum):
    total = "total"
    matched = "matched"
    missing = "missing"
    downloaded = "downloaded"


class RecommendationProvider(str, enum.Enum):
    lastfm = "lastfm"


class RecommendationStrategy(str, enum.Enum):
    top_tracks = "top_tracks"
    recent_tracks = "recent_tracks"
    mixed = "mixed"
    blend = "blend"


class Recommendation(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    username: str = Field(max_length=128, nullable=False, unique=True, index=True)
    strategy: RecommendationStrategy = Field(nullable=False)
    lastfm_username: str = Field(max_length=128, nullable=False)
    requested_count: int = Field(default=50, nullable=False)
    cron_expression: str = Field(default="", max_length=128, nullable=False)
    is_public: bool = Field(default=False, nullable=False)
    playlist_name: str = Field(default="", max_length=256, nullable=False)
    blend_users: list[dict[str, str]] | None = Field(
        default=None, sa_type=sa.JSON, nullable=True
    )

    def get_blend_users(self) -> list[BlendUser] | None:
        if self.blend_users is None:
            return None
        return [BlendUser.from_dict(user) for user in self.blend_users]


class RecommendationSession(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    username: str = Field(max_length=128, nullable=False, index=True)
    provider: RecommendationProvider = Field(nullable=False, index=True)

    strategy: RecommendationStrategy = Field(nullable=False)
    requested_count: int = Field(default=50, nullable=False)
    generated_count: int = Field(default=0, nullable=False)
    blend_users: list[dict[str, str]] | None = Field(
        default=None, sa_type=sa.JSON, nullable=True
    )

    def get_blend_users(self) -> list[BlendUser] | None:
        if self.blend_users is None:
            return None
        return [BlendUser.from_dict(user) for user in self.blend_users]

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

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "username": self.username,
            "provider": self.provider.value,
            "strategy": self.strategy.value,
            "requested_count": self.requested_count,
            "generated_count": self.generated_count,
            "blend_users": self.blend_users,
            "started_at": format_time_with_locale(self.started_at),
            "finished_at": format_time_with_locale(self.finished_at),
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "error_message": self.error_message,
            "created_at": format_time_with_locale(self.created_at),
            "updated_at": format_time_with_locale(self.updated_at),
        }


class RecommendationSessionTrack(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    recommendation_session_id: uuid.UUID = Field(
        foreign_key="recommendationsession.id", nullable=False, index=True
    )
    session: RecommendationSession = Relationship(back_populates="tracks")

    name: str = Field(max_length=256, nullable=False)
    type: RecommendationTrackType = Field(nullable=False)
