import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlmodel import Field

from slidegen.models.base import Base
from slidegen.utils.time import now_tz_datetime


class ImageAsset(Base, table=True):
    """Image asset"""

    __tablename__ = "image_assets"
    __comment__ = "image asset table"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, description="Image id")
    created_at: datetime = Field(
        description="Image created at",
        sa_column=Column(DateTime(timezone=True), nullable=False, default=now_tz_datetime),
    )
    is_uploaded: bool = Field(
        default=False, description="Is uploaded", sa_column=Column(Boolean, nullable=False, default=False)
    )
    path: str = Field(description="Image path")
    extras: dict[str, Any] | None = Field(sa_column=Column(JSON), default=None, description="Image extras")
