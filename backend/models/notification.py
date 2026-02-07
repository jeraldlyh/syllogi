import enum
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from lib.mixin import SerializerMixin
from models.db import db


class Channel(enum.Enum):
    discord = "discord"


class Notification(db.Model, SerializerMixin):
    __tablename__ = "notification"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel = db.Column(sa.Enum(Channel, name="channel"), nullable=False, unique=True)
    webhook_url = db.Column(db.String(1024), nullable=False)
    enabled = db.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))

    created_at = db.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at = db.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
