import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Column, Field

from slidegen.models.base import Base
from slidegen.utils.time import now_datetime


class TaskOwnership(Base, table=True):
    """Track task ownership for access control"""

    __tablename__ = "task_ownership"

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(max_length=255, unique=True, index=True, description="Celery task ID")
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, description="User who created the task")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=now_datetime),
        description="Task creation time",
    )
