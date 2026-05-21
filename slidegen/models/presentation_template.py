import uuid
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field

from slidegen.models.base import Base


class PresentationTemplateModel(Base, table=True):
    __tablename__ = "presentation_templates"
    __table_args__ = {"comment": "User uploaded PPTX templates"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    original_filename: str = Field(max_length=500)
    file_path: str = Field(max_length=1000)
    file_size: int
    content_type: str | None = Field(default=None, max_length=100)
    file_hash: str = Field(max_length=64, index=True)
    template_key: str = Field(max_length=100, index=True, unique=True)
    slide_count: int = Field(default=0)
    status: str = Field(default="review_required", max_length=50, index=True)
    role_profile: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    warnings: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    is_deleted: bool = Field(default=False, index=True)
