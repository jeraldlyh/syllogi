import enum
import uuid

from sqlmodel import Field, SQLModel

from lib.utils import format_time_with_locale
from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin


class NotificationChannel(enum.Enum):
    discord = "discord"


class Notification(
    TimestampMixin,
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

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "channel": self.channel.value,
            "webhook_url": self.webhook_url,
            "enabled": self.enabled,
            "created_at": format_time_with_locale(self.created_at),
            "updated_at": format_time_with_locale(self.updated_at),
        }
