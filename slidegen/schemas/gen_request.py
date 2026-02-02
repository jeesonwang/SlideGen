import uuid
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from slidegen.models.llm_config import LLMProvider
from slidegen.schemas.llm_config import LLMConfigTest
from slidegen.schemas.theme import PresentationTheme


class Tone(str, Enum):
    DEFAULT = "default"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FUNNY = "funny"
    EDUCATIONAL = "educational"
    SALES_PITCH = "sales_pitch"


class Verbosity(str, Enum):
    CONCISE = "concise"
    STANDARD = "standard"
    TEXT_HEAVY = "text-heavy"


class BaseGenerationRequest(BaseModel):
    """Base class for generation requests with shared fields"""

    # Content related fields
    content: str = Field(..., description="The content/topic for generation")
    instructions: str | None = Field(default=None, description="Additional instructions for generation")
    tone: Tone = Field(default=Tone.DEFAULT, description="The tone to use for the text")
    verbosity: Verbosity = Field(default=Verbosity.STANDARD, description="How verbose the content should be")
    web_search: bool = Field(default=False, description="Whether to enable web search")
    n_slides: int = Field(default=8, description="Number of slides/sections to generate")
    language: str = Field(default="English", description="Language for the content")

    # File references (for knowledge base)
    files: list[str] | None = Field(default=None, description="File IDs to use as reference")

    # User and configuration related fields
    user_id: uuid.UUID = Field(..., description="User ID, for getting the LLM config")
    llm_config_id: uuid.UUID | None = Field(default=None, description="LLM config ID")
    embedding_config_id: uuid.UUID | None = Field(default=None, description="Embedding config ID")

    # Session related fields
    session_id: uuid.UUID | None = Field(
        default=None,
        description="Session ID for this generation task. If None, a new session will be created automatically.",
    )


class GeneratePresentationRequest(BaseGenerationRequest):
    """Generate presentation request"""

    # Additional content fields
    slides_markdown: list[str] | None = Field(default=None, description="The markdown for the slides")

    # Template and output related fields
    template: str = Field(default="general", description="Template to use for the presentation")
    include_table_of_contents: bool = Field(default=False, description="Whether to include a table of contents")
    include_title_slide: bool = Field(default=True, description="Whether to include a title slide")
    export_as: Literal["pptx", "pdf"] = Field(default="pptx", description="Export format")

    # Theme related fields
    theme: PresentationTheme | None = Field(default=None, description="Optional theme to apply to the presentation")
    theme_preset: str | None = Field(
        default=None, description="Optional theme preset name (e.g., 'sunset_boulevard', 'ocean_breeze')"
    )


class GenerateMarkdownRequest(BaseGenerationRequest):
    """Request for generating markdown content only (without PPT conversion)"""

    pass


class MarkdownToPPTRequest(BaseModel):
    """Request for generating PPT from markdown content"""

    markdown_content: str = Field(..., description="The markdown content to convert to PPT")
    template: str = Field(default="general", description="Template to use for the presentation")
    export_as: Literal["pptx", "pdf"] = Field(default="pptx", description="Export format")

    # Theme related fields
    theme: PresentationTheme | None = Field(default=None, description="Optional theme to apply to the presentation")
    theme_preset: str | None = Field(
        default=None, description="Optional theme preset name (e.g., 'sunset_boulevard', 'ocean_breeze')"
    )


class LLMConfigRequest(LLMConfigTest):
    provider: LLMProvider = LLMProvider.CUSTOM
