import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from slidegen.models.base import Base


# Shared properties
class FileMetadataBase(SQLModel):
    filename: str = Field(max_length=500, description="Original filename")
    file_size: int = Field(description="File size in bytes")
    file_path: str = Field(max_length=1000, description="Storage path on filesystem")
    content_type: str | None = Field(default=None, max_length=100, description="MIME type")
    file_hash: str | None = Field(default=None, max_length=64, description="SHA256 hash for deduplication")
    parsed: bool = Field(default=False, description="Whether file has been parsed")
    parse_error: str | None = Field(default=None, max_length=2000, description="Parse error message")


# Properties for API creation
class FileMetadataCreate(FileMetadataBase):
    session_id: uuid.UUID


# Properties for API update
class FileMetadataUpdate(SQLModel):
    filename: str | None = Field(default=None, max_length=500)
    parsed: bool | None = Field(default=None)
    parse_error: str | None = Field(default=None)


# Properties for API response
class FileMetadataPublic(FileMetadataBase):
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    create_time: datetime
    update_time: datetime


class FileMetadatasPublic(SQLModel):
    data: list[FileMetadataPublic]
    count: int


# Database model
class FileMetadataModel(Base, table=True):
    __tablename__ = "file_metadata"
    __table_args__ = {"comment": "File metadata tracking for session-scoped files"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, description="File ID")
    session_id: uuid.UUID = Field(foreign_key="sessions.id", index=True, description="Session ID")
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, description="User ID (denormalized for performance)")
    filename: str = Field(max_length=500, description="Original filename")
    file_size: int = Field(description="File size in bytes")
    file_path: str = Field(max_length=1000, description="Storage path")
    content_type: str | None = Field(default=None, max_length=100)
    file_hash: str | None = Field(default=None, max_length=64, index=True, description="SHA256 hash")
    parsed: bool = Field(default=False, description="Parse status")
    parse_error: str | None = Field(default=None, max_length=2000)

    # Relationship
    session: "SessionModel" = Relationship(back_populates="files")  # type: ignore # noqa: F821
