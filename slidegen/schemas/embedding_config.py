from typing import Any

from pydantic import BaseModel, Field

from slidegen.models.embedding_config import EmbeddingProvider


class EmbeddingConfigTest(BaseModel):
    """Test Embedding configuration schema"""

    provider: EmbeddingProvider = Field(description="Embedding provider")
    model_id: str = Field(description="Model ID")
    api_key: str | None = Field(default=None, description="API key")
    base_url: str | None = Field(default=None, description="API base URL")
    dimensions: int | None = Field(default=None, ge=1, description="Embedding dimensions")
    extra_params: dict[str, Any] | None = Field(default=None, description="Extra parameters")
    test_text: str = Field(default="This is a test sentence for embedding.", description="Test text")


class EmbeddingConfigTestResult(BaseModel):
    """Embedding configuration test result"""

    success: bool = Field(description="Test success")
    embedding_dimension: int | None = Field(default=None, description="Actual embedding dimension")
    error: str | None = Field(default=None, description="Error information")
    latency: float | None = Field(default=None, description="Response latency (seconds)")


class AvailableEmbeddingModels(BaseModel):
    """Available embedding models list"""

    provider: EmbeddingProvider = Field(description="Provider")
    models: list[dict[str, Any]] = Field(description="Models list")


class EmbeddingProviderInfo(BaseModel):
    """Embedding provider information"""

    provider: EmbeddingProvider = Field(description="Provider")
    name: str = Field(description="Provider name")
    description: str = Field(description="Provider description")
    requires_api_key: bool = Field(description="Whether to require API key")
    supports_custom_base_url: bool = Field(description="Whether to support custom base URL")
    default_base_url: str | None = Field(default=None, description="Default base URL")
    documentation_url: str | None = Field(default=None, description="Documentation link")


class EmbeddingProvidersInfo(BaseModel):
    """All Embedding providers information"""

    providers: list[EmbeddingProviderInfo] = Field(description="Providers list")


# Preset provider information
EMBEDDING_PROVIDER_INFO = {
    EmbeddingProvider.OPENAI: EmbeddingProviderInfo(
        provider=EmbeddingProvider.OPENAI,
        name="OpenAI",
        description="OpenAI official embedding API, including text-embedding-3-large, text-embedding-3-small, etc.",
        requires_api_key=True,
        supports_custom_base_url=True,
        default_base_url="https://api.openai.com/v1",
        documentation_url="https://platform.openai.com/docs/guides/embeddings",
    ),
    EmbeddingProvider.AZURE_OPENAI: EmbeddingProviderInfo(
        provider=EmbeddingProvider.AZURE_OPENAI,
        name="Azure OpenAI",
        description="OpenAI embedding service on Microsoft Azure platform",
        requires_api_key=True,
        supports_custom_base_url=True,
        default_base_url=None,
        documentation_url="https://learn.microsoft.com/en-us/azure/ai-services/openai/",
    ),
    EmbeddingProvider.OLLAMA: EmbeddingProviderInfo(
        provider=EmbeddingProvider.OLLAMA,
        name="Ollama",
        description="Open-source embedding models deployed locally",
        requires_api_key=False,
        supports_custom_base_url=True,
        default_base_url="http://localhost:11434",
        documentation_url="https://ollama.ai/docs",
    ),
    EmbeddingProvider.CUSTOM: EmbeddingProviderInfo(
        provider=EmbeddingProvider.CUSTOM,
        name="Custom",
        description="Custom embedding API service",
        requires_api_key=True,
        supports_custom_base_url=True,
        default_base_url=None,
        documentation_url=None,
    ),
}
