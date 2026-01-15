import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from slidegen.models.base import Base


class SessionStatus(str, Enum):
    """Session status enumeration"""

    ACTIVE = "active"  # Session is active and can be used
    COMPLETED = "completed"  # PPT generation completed
    FAILED = "failed"  # Generation failed
    ARCHIVED = "archived"  # User archived the session
    DELETED = "deleted"  # Soft deleted (for retention policy)


# Shared properties
class SessionBase(SQLModel):
    title: str = Field(max_length=500, description="Session title/description")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Session status")
    topic: str | None = Field(default=None, description="PPT generation topic/content")
    extra_data: dict[str, Any] | None = Field(
        sa_column=Column(JSON), default=None, description="Session extra data (e.g., generation params)"
    )


# Properties for API creation
class SessionCreate(SessionBase):
    pass


# Properties for API update
class SessionUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=500)
    status: SessionStatus | None = Field(default=None)
    topic: str | None = Field(default=None)
    extra_data: dict[str, Any] | None = Field(default=None)


# Properties for API response
class SessionPublic(SessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    file_count: int = Field(default=0, description="Number of files in session")
    message_count: int = Field(default=0, description="Number of chat messages")
    create_time: datetime
    update_time: datetime


class SessionsPublic(SQLModel):
    data: list[SessionPublic]
    count: int


# Database model
class SessionModel(Base, table=True):
    __tablename__ = "sessions"
    __table_args__ = {"comment": "User sessions for PPT generation tasks"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, description="Session ID")
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, description="User ID")
    title: str = Field(max_length=500, description="Session title")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, index=True, description="Session status")
    topic: str | None = Field(default=None, description="PPT topic")
    extra_data: dict[str, Any] | None = Field(sa_column=Column(JSON), default=None)

    # Relationships (SQLModel Relationship for ORM navigation)
    # Note: Forward references will be resolved when file_metadata and chat_message models are imported
    files: list["FileMetadataModel"] = Relationship(  # type: ignore # noqa: F821
        back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    messages: list["ChatMessageModel"] = Relationship(  # type: ignore # noqa: F821
        back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
