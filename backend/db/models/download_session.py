import enum
import uuid
from datetime import datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin
from lib.utils import format_time_with_locale, get_now


class DownloadSessionStatus(str, enum.Enum):
    pending = "pending"
    downloading = "downloading"
    completed = "completed"
    failed = "failed"
    existed = "existed"


class DownloadSession(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    artist_name: str = Field(max_length=512, nullable=False)
    track_name: str = Field(max_length=512, nullable=False)
    image_url: str = Field(max_length=2048, nullable=False)

    status: DownloadSessionStatus = Field(nullable=False, index=True)

    started_at: datetime = Field(
        default_factory=get_now,
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )
    finished_at: datetime | None = Field(
        default=None,
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        nullable=True,
    )

    error_message: str | None = Field(default=None, max_length=1024, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "artist_name": self.artist_name,
            "track_name": self.track_name,
            "image_url": self.image_url,
            "status": self.status.value,
            "started_at": format_time_with_locale(self.started_at),
            "finished_at": format_time_with_locale(self.finished_at),
            "error_message": self.error_message,
            "created_at": format_time_with_locale(self.created_at),
            "updated_at": format_time_with_locale(self.updated_at),
        }
