from datetime import datetime

from sqlmodel import Field, SQLModel

from lib.mixin.metadata import TimestampMixin


class TimestampTestModel(TimestampMixin, SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default="")


class TestTimestampMixin:
    def test_created_at_set_on_creation(self):
        model = TimestampTestModel(name="test")

        assert model.created_at is not None
        assert isinstance(model.created_at, datetime)

    def test_updated_at_set_on_creation(self):
        model = TimestampTestModel(name="test")

        assert model.updated_at is not None
        assert isinstance(model.updated_at, datetime)

    def test_created_at_and_updated_at_are_close(self):
        model = TimestampTestModel(name="test")
        diff = abs((model.updated_at - model.created_at).total_seconds())

        assert diff < 1.0

    def test_field_names_present(self):
        model = TimestampTestModel(name="test")

        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")
