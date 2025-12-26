from datetime import datetime

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """File upload response"""

    file_id: str = Field(..., description="File unique identifier")
    filename: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size (bytes)")
    content_type: str | None = Field(default=None, description="File MIME type")
    upload_time: datetime = Field(default_factory=datetime.now, description="Upload time")
    message: str = Field(default="File uploaded successfully", description="Response message")


class FileMetadata(BaseModel):
    """File metadata"""

    file_id: str = Field(..., description="File unique identifier")
    filename: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size (bytes)")
    file_path: str = Field(..., description="File storage path")
    content_type: str | None = Field(default=None, description="File MIME type")
    upload_time: datetime = Field(default_factory=datetime.now, description="Upload time")
    user_id: str | None = Field(default=None, description="Upload user ID")
    parsed: bool = Field(default=False, description="Whether parsed")
    parse_error: str | None = Field(default=None, description="Parse error information")


class ParsedFileContent(BaseModel):
    """Parsed file content"""

    file_id: str = Field(..., description="File unique identifier")
    filename: str = Field(..., description="Original file name")
    content: str = Field(..., description="Parsed Markdown content")
    word_count: int = Field(default=0, description="Word count")
    parse_time: datetime = Field(default_factory=datetime.now, description="Parse time")


class MultiFileUploadResponse(BaseModel):
    """Multi file upload response"""

    success: bool = Field(..., description="Whether all files are uploaded successfully")
    files: list[FileUploadResponse] = Field(..., description="Uploaded files list")
    failed_files: list[dict[str, str]] = Field(default_factory=list, description="Failed files list")
    message: str = Field(default="All files uploaded successfully", description="Response message")
