from datetime import datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlmodel import Field
from lib.utils import get_now


class TimestampMixin:
    created_at: datetime = Field(
        default=get_now(),
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )

    updated_at: datetime = Field(
        default=get_now(),
        sa_type=cast(type[Any], sa.DateTime(timezone=True)),
        sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )
