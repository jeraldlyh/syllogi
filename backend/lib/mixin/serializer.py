from typing import Any, Dict, Optional

from pydantic import ConfigDict
from sqlmodel import SQLModel


class SerializerMixin(SQLModel):
    model_config = ConfigDict(use_enum_values=True)

    def to_dict(
        self,
        *,
        exclude: Optional[set[str]] = None,
    ) -> Dict[str, Any]:
        return self.model_dump(
            exclude=exclude or set(),
        )
