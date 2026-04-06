import uuid
from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin
from sqlmodel import Field, SQLModel


class User(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    username: str = Field(max_length=128, nullable=False, unique=True, index=True)
    password: str = Field(max_length=256, nullable=False)
