import uuid
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from slidegen.models.llm_config import LLMProvider
from slidegen.schemas.llm_config import LLMConfigTest


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


class GeneratePresentationRequest(BaseModel):
    """Generate presentation request"""

    # Content related fields
    content: str = Field(..., description="The content for generating the presentation")
    slides_markdown: list[str] | None = Field(default=None, description="The markdown for the slides")
    instructions: str | None = Field(default=None, description="The instruction for generating the presentation")
    tone: Tone = Field(default=Tone.DEFAULT, description="The tone to use for the text")
    verbosity: Verbosity = Field(default=Verbosity.STANDARD, description="How verbose the presentation should be")
    web_search: bool = Field(default=False, description="Whether to enable web search")
    n_slides: int = Field(default=8, description="Number of slides to generate")
    language: str = Field(default="English", description="Language for the presentation")

    # Template and output related fields
    template: str = Field(default="general", description="Template to use for the presentation")
    include_table_of_contents: bool = Field(default=False, description="Whether to include a table of contents")
    include_title_slide: bool = Field(default=True, description="Whether to include a title slide")
    files: list[str] | None = Field(default=None, description="File IDs to use for the presentation")
    export_as: Literal["pptx", "pdf"] = Field(default="pptx", description="Export format")

    # User and configuration related fields
    user_id: uuid.UUID = Field(..., description="User ID, for getting the LLM config")
    llm_config_id: uuid.UUID | None = Field(default=None, description="LLM config ID")


class LLMConfigRequest(LLMConfigTest):
    provider: LLMProvider = LLMProvider.CUSTOM
