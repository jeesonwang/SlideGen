import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from slidegen.models.base import Base


class MessageRole(str, Enum):
    """Message role enumeration"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Shared properties
class ChatMessageBase(SQLModel):
    role: MessageRole = Field(description="Message role")
    content: str = Field(description="Message content")
    extra_data: dict[str, Any] | None = Field(sa_column=Column(JSON), default=None, description="Message extra data")


# Properties for API creation
class ChatMessageCreate(ChatMessageBase):
    session_id: uuid.UUID


# Properties for API response
class ChatMessagePublic(ChatMessageBase):
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    create_time: datetime


class ChatMessagesPublic(SQLModel):
    data: list[ChatMessagePublic]
    count: int


# Database model
class ChatMessageModel(Base, table=True):
    __tablename__ = "chat_messages"
    __table_args__ = {"comment": "Chat conversation history for sessions"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, description="Message ID")
    session_id: uuid.UUID = Field(foreign_key="sessions.id", index=True, description="Session ID")
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, description="User ID")
    role: MessageRole = Field(description="Message role")
    content: str = Field(description="Message content")
    extra_data: dict[str, Any] | None = Field(sa_column=Column(JSON), default=None, description="Extra data")

    # Relationship
    session: "SessionModel" = Relationship(back_populates="messages")  # type: ignore # noqa: F821
