from datetime import datetime

from sqlmodel import Field, SQLModel
from sqlmodel._compat import SQLModelConfig

from slidegen.utils.time import now_datetime


class Base(SQLModel):
    """Base model for all models"""

    __abstract__ = True

    model_config = SQLModelConfig(
        arbitrary_types_allowed=True, from_attributes=True, validate_assignment=True
    )  # pydantic v2

    create_time: datetime = Field(
        default_factory=now_datetime,
        index=True,
        nullable=False,
        sa_column_kwargs={"comment": "Create time"},
    )
    update_time: datetime = Field(
        default_factory=now_datetime,
        index=True,
        nullable=False,
        sa_column_kwargs={"comment": "Update time"},
    )
    # is_delete: bool = Field(default=False, description="Is deleted")
