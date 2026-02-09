import enum
import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
from lib.mixin.serializer import SerializerMixin


class NotificationChannel(enum.Enum):
    discord = "discord"


class Notification(
    SerializerMixin,
    SQLModel,
    table=True,
):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    channel: NotificationChannel = Field(
        default=NotificationChannel.discord, unique=True, nullable=False
    )
    webhook_url: str = Field(default="", max_length=1024, nullable=False)
    enabled: bool = Field(default=True, nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
