from typing import Any, cast

from pydantic import ConfigDict
from sqlmodel import SQLModel


class SerializerMixin(SQLModel):
    model_config = cast(Any, ConfigDict(use_enum_values=True))

    def to_dict(
        self,
        *,
        exclude: set[str] | None = None,
    ) -> dict[str, Any]:
        return self.model_dump(
            exclude=exclude or set(),
        )
