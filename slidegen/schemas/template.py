"""Template schemas."""

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class TemplateSource(str, Enum):
    BUILTIN = "builtin"
    USER = "user"


class TemplateRoleAssignmentResponse(BaseModel):
    role: str = Field(..., description="Template role: cover, catalog, chapter, content, or end")
    slide_index: int = Field(..., description="Zero-based source slide index")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Heuristic confidence")
    reason: str = Field(..., description="Why the role was assigned")


class TemplateProfileResponse(BaseModel):
    slide_count: int = Field(..., ge=1, description="Number of slides in the source template")
    status: str = Field(..., description="ready, review_required, or failed")
    assignments: list[TemplateRoleAssignmentResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_roles: list[str] = Field(default_factory=list)


class Template(BaseModel):
    """Presentation template information."""

    id: str = Field(..., description="Template ID used in generation requests")
    name: str = Field(..., description="Template display name")
    thumbnail: str | None = Field(default=None, description="Template thumbnail URL")
    source: TemplateSource = Field(default=TemplateSource.BUILTIN, description="Template source")
    profile_status: str | None = Field(default=None, description="Uploaded template profile status")
    role_profile: TemplateProfileResponse | None = Field(default=None, description="Uploaded template role profile")


class UserTemplateUploadResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Uploaded template database ID")
    template_key: str = Field(..., description="Template key used in generation requests")
    name: str = Field(..., description="Template display name")
    original_filename: str = Field(..., description="Original uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    profile: TemplateProfileResponse = Field(..., description="Automatic role profile")
    message: str = Field(default="Template uploaded successfully")


class UserTemplateDeleteResponse(BaseModel):
    template_key: str = Field(..., description="Deleted uploaded template key")
    message: str = Field(default="Template deleted successfully")
