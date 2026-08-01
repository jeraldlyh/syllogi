import enum

from sqlmodel import Field, SQLModel

from lib.mixin.serializer import SerializerMixin


class Status(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class SerializerTestModel(SerializerMixin, SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default="")
    status: Status = Field(default=Status.active)


class TestSerializerMixin:
    def test_to_dict_returns_all_fields(self):
        name = "Alice"
        model = SerializerTestModel(id=1, name=name, status=Status.active)
        result = model.to_dict()

        assert result["id"] == 1
        assert result["name"] == name
        assert result["status"] == Status.active.value

    def test_to_dict_returns_enum_object(self):
        model = SerializerTestModel(status=Status.inactive)
        result = model.to_dict()

        assert result["status"] == Status.inactive

    def test_to_dict_exclude_fields(self):
        name = "Alice"
        model = SerializerTestModel(id=1, name=name, status=Status.active)
        result = model.to_dict(exclude={"id"})

        assert "id" not in result
        assert result["name"] == name

    def test_to_dict_exclude_multiple_fields(self):
        name = "Alice"
        model = SerializerTestModel(id=1, name=name, status=Status.active)
        result = model.to_dict(exclude={"id", "status"})

        assert "id" not in result
        assert "status" not in result
        assert result["name"] == name

    def test_to_dict_empty_model(self):
        model = SerializerTestModel()
        result = model.to_dict()

        assert result["name"] == ""
        assert result["status"] == Status.active.value
