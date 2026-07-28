import uuid

from sqlmodel import Field, SQLModel

from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin


class User(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    oauth_id: str | None = Field(max_length=256, nullable=True, unique=True, index=True)
    username: str = Field(max_length=128, nullable=False, unique=True, index=True)
    password: str = Field(max_length=256, nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
