import uuid
from enum import Enum
from typing import Any

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from slidegen.models.base import Base


class EmbeddingProvider(str, Enum):
    """Embedding provider enumeration"""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    CUSTOM = "custom"


# Shared properties
class EmbeddingConfigBase(SQLModel):
    name: str = Field(default="", max_length=255, description="Configuration name")
    provider: EmbeddingProvider = Field(description="Embedding provider")
    model_id: str = Field(..., max_length=255, description="Model ID")
    api_key: str | None = Field(default=None, max_length=500, description="API key")
    base_url: str | None = Field(default=None, max_length=500, description="API base URL")
    dimensions: int | None = Field(default=None, ge=1, description="Embedding dimensions (optional)")
    description: str | None = Field(default=None, max_length=1000, description="Configuration description")
    extra_params: dict[str, Any] | None = Field(default=None, description="Extra parameters")
    is_active: bool = Field(default=True, description="Whether to enable")
    is_default: bool = Field(default=False, description="Whether to be the default configuration")


# Properties to receive via API on creation
class EmbeddingConfigCreate(EmbeddingConfigBase):
    user_id: uuid.UUID = Field(description="User ID")


# Properties to receive via API on update
# All fields are optional for partial updates
class EmbeddingConfigUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255, description="Configuration name")
    provider: EmbeddingProvider | None = Field(default=None, description="Embedding provider")
    model_id: str | None = Field(default=None, max_length=255, description="Model ID")
    api_key: str | None = Field(default=None, max_length=500, description="API key")
    base_url: str | None = Field(default=None, max_length=500, description="API base URL")
    dimensions: int | None = Field(default=None, ge=1, description="Embedding dimensions (optional)")
    is_active: bool | None = Field(default=None, description="Whether to enable")
    is_default: bool | None = Field(default=None, description="Whether to be the default configuration")
    description: str | None = Field(default=None, max_length=1000, description="Configuration description")
    extra_params: dict[str, Any] | None = Field(default=None, description="Extra parameters")


# Properties to return via API
class EmbeddingConfigPublic(EmbeddingConfigBase):
    id: uuid.UUID
    user_id: uuid.UUID
    # For security, do not return API key
    api_key: str | None = Field(default=None, description="API key (hidden)")

    @field_validator("api_key", mode="before")
    @classmethod
    def mask_api_key(cls, v: str | None) -> str | None:
        if v:
            return "***" + v[-4:] if len(v) > 4 else "***"
        return None


class EmbeddingConfigsPublic(SQLModel):
    data: list[EmbeddingConfigPublic]
    count: int


# Database model
class EmbeddingConfigModel(Base, EmbeddingConfigBase, table=True):
    __tablename__ = "embedding_configs"
    __comment__ = "Embedding configuration table"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, description="Configuration ID")
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, description="User ID")
    # Override extra_params to use JSON column for database
    extra_params: dict[str, Any] | None = Field(sa_column=Column(JSON), default=None, description="Extra parameters")


DEFAULT_EMBEDDING_CONFIGS = {
    EmbeddingProvider.OPENAI: [
        {"model_id": "text-embedding-3-large", "name": "Text Embedding 3 Large", "dimensions": 3072},
        {"model_id": "text-embedding-3-small", "name": "Text Embedding 3 Small", "dimensions": 1536},
        {"model_id": "text-embedding-ada-002", "name": "Ada 002", "dimensions": 1536},
    ],
    EmbeddingProvider.OLLAMA: [
        {"model_id": "nomic-embed-text", "name": "Nomic Embed Text", "dimensions": 768},
        {"model_id": "mxbai-embed-large", "name": "MxBai Embed Large", "dimensions": 1024},
        {"model_id": "all-minilm", "name": "All-MiniLM-L6-v2", "dimensions": 384},
    ],
}
