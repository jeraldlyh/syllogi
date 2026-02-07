from datetime import datetime
from uuid import UUID as _UUID
import enum
from sqlalchemy.inspection import inspect


class SerializerMixin:
    __serialize_include__ = None
    __serialize_exclude__ = set()

    def to_dict(self):
        mapper = inspect(self).mapper
        columns = [column.key for column in mapper.column_attrs]
        include = set(self.__serialize_include__ or columns) - set(
            self.__serialize_exclude__
        )
        out = {}
        for key in include:
            val = getattr(self, key)
            out[key] = _coerce_json(val)
        return out


def _coerce_json(val):
    if isinstance(val, enum.Enum):
        return val.value
    if isinstance(val, _UUID):
        return str(val)
    if isinstance(val, datetime):
        return val.isoformat()
    return val
