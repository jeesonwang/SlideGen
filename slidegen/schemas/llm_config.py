from typing import Any

from pydantic import BaseModel, Field

from slidegen.models.llm_config import LLMProvider


class LLMConfigTest(BaseModel):
    """Test LLM configuration schema"""

    provider: LLMProvider = Field(description="LLM provider")
    model_id: str = Field(description="Model ID")
    api_key: str | None = Field(default=None, description="API key")
    base_url: str | None = Field(default=None, description="API base URL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature parameter")
    max_tokens: int | None = Field(default=None, ge=1, description="Max tokens")
    extra_params: dict[str, Any] | None = Field(default=None, description="Extra parameters")
    test_prompt: str = Field(default="Hello, how are you?", description="Test prompt")


class LLMConfigTestResult(BaseModel):
    """LLM configuration test result"""

    success: bool = Field(description="Test success")
    response: str | None = Field(default=None, description="Model response")
    error: str | None = Field(default=None, description="Error information")
    latency: float | None = Field(default=None, description="Response latency (seconds)")


class AvailableModels(BaseModel):
    """Available models list"""

    provider: LLMProvider = Field(description="Provider")
    models: list[dict[str, str]] = Field(description="Models list")


class LLMProviderInfo(BaseModel):
    """LLM provider information"""

    provider: LLMProvider = Field(description="Provider")
    name: str = Field(description="Provider name")
    description: str = Field(description="Provider description")
    requires_api_key: bool = Field(description="Whether to require API key")
    supports_custom_base_url: bool = Field(description="Whether to support custom base URL")
    default_base_url: str | None = Field(default=None, description="Default base URL")
    documentation_url: str | None = Field(default=None, description="Documentation link")


class LLMProvidersInfo(BaseModel):
    """All LLM providers information"""

    providers: list[LLMProviderInfo] = Field(description="Providers list")


# Preset provider information
PROVIDER_INFO = {
    LLMProvider.OPENAI: LLMProviderInfo(
        provider=LLMProvider.OPENAI,
        name="OpenAI",
        description="OpenAI official API, including GPT-4, GPT-3.5, etc.",
        requires_api_key=True,
        supports_custom_base_url=True,
        default_base_url="https://api.openai.com/v1",
        documentation_url="https://platform.openai.com/docs",
    ),
    LLMProvider.OPENROUTER: LLMProviderInfo(
        provider=LLMProvider.OPENROUTER,
        name="OpenRouter",
        description="Aggregates multiple LLM APIs, including OpenAI, Anthropic, Meta, etc.",
        requires_api_key=True,
        supports_custom_base_url=False,
        default_base_url="https://openrouter.ai/api/v1",
        documentation_url="https://openrouter.ai/docs",
    ),
    LLMProvider.ANTHROPIC: LLMProviderInfo(
        provider=LLMProvider.ANTHROPIC,
        name="Anthropic",
        description="Anthropic official API, including Claude series models",
        requires_api_key=True,
        supports_custom_base_url=True,
        default_base_url="https://api.anthropic.com",
        documentation_url="https://docs.anthropic.com",
    ),
    LLMProvider.AZURE_OPENAI: LLMProviderInfo(
        provider=LLMProvider.AZURE_OPENAI,
        name="Azure OpenAI",
        description="OpenAI service on Microsoft Azure platform",
        requires_api_key=True,
        supports_custom_base_url=True,
        default_base_url=None,
        documentation_url="https://learn.microsoft.com/en-us/azure/ai-services/openai/",
    ),
    LLMProvider.OLLAMA: LLMProviderInfo(
        provider=LLMProvider.OLLAMA,
        name="Ollama",
        description="Open-source LLM service deployed locally",
        requires_api_key=False,
        supports_custom_base_url=True,
        default_base_url="http://localhost:11434",
        documentation_url="https://ollama.ai/docs",
    ),
    LLMProvider.CUSTOM: LLMProviderInfo(
        provider=LLMProvider.CUSTOM,
        name="Custom",
        description="Custom LLM API service",
        requires_api_key=True,
        supports_custom_base_url=True,
        default_base_url=None,
        documentation_url=None,
    ),
}
