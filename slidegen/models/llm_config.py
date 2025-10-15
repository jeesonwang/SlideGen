import uuid
from enum import Enum
from typing import Any

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from slidegen.models.base import Base


class LLMProvider(str, Enum):
    """LLM provider enumeration"""

    OPENAI = "openai"
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    CUSTOM = "custom"


# Shared properties
class LLMConfigBase(SQLModel):
    name: str = Field(default="", max_length=255, description="Configuration name")
    provider: LLMProvider = Field(description="LLM provider")
    model_id: str = Field(..., max_length=255, description="Model ID")
    api_key: str | None = Field(default=None, max_length=500, description="API key")
    base_url: str | None = Field(default=None, max_length=500, description="API base URL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature parameter")
    max_tokens: int = Field(default=4096, ge=1, description="Max tokens")
    description: str | None = Field(default=None, max_length=1000, description="Configuration description")
    extra_params: dict[str, Any] | None = Field(default=None, description="Extra parameters")
    is_active: bool = Field(default=True, description="Whether to enable")
    is_default: bool = Field(default=False, description="Whether to be the default configuration")


# Properties to receive via API on creation
class LLMConfigCreate(LLMConfigBase):
    user_id: uuid.UUID = Field(description="User ID")


# Properties to receive via API on update
# All fields are optional for partial updates
class LLMConfigUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255, description="Configuration name")
    provider: LLMProvider | None = Field(default=None, description="LLM provider")
    model_id: str | None = Field(default=None, max_length=255, description="Model ID")
    api_key: str | None = Field(default=None, max_length=500, description="API key")
    base_url: str | None = Field(default=None, max_length=500, description="API base URL")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Temperature parameter")
    max_tokens: int | None = Field(default=None, ge=1, description="Max tokens")
    is_active: bool | None = Field(default=None, description="Whether to enable")
    is_default: bool | None = Field(default=None, description="Whether to be the default configuration")
    description: str | None = Field(default=None, max_length=1000, description="Configuration description")
    extra_params: dict[str, Any] | None = Field(default=None, description="Extra parameters")


# Properties to return via API
class LLMConfigPublic(LLMConfigBase):
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


class LLMConfigsPublic(SQLModel):
    data: list[LLMConfigPublic]
    count: int


# Database model
class LLMConfigModel(Base, LLMConfigBase, table=True):
    __tablename__ = "llm_configs"
    __comment__ = "LLM configuration table"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, description="Configuration ID")
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, description="User ID")
    # Override extra_params to use JSON column for database
    extra_params: dict[str, Any] | None = Field(sa_column=Column(JSON), default=None, description="Extra parameters")


DEFAULT_MODEL_CONFIGS = {
    LLMProvider.OPENAI: [
        {"model_id": "gpt-4o", "name": "GPT-4o"},
        {"model_id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"model_id": "gpt-5", "name": "GPT-5"},
        {"model_id": "gpt-5-mini", "name": "GPT-5 Mini"},
    ],
    LLMProvider.OPENROUTER: [
        {"model_id": "openai/gpt-4o", "name": "GPT-4o (OpenRouter)"},
        {"model_id": "openai/gpt-4o-mini", "name": "GPT-4o Mini (OpenRouter)"},
        {"model_id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
        {"model_id": "meta-llama/llama-3.1-405b-instruct", "name": "Llama 3.1 405B"},
    ],
    LLMProvider.ANTHROPIC: [
        {"model_id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
        {"model_id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
        {"model_id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
    ],
}
