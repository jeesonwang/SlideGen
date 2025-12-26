import time
from typing import Any

from agno.knowledge.embedder.azure_openai import AzureOpenAIEmbedder
from agno.knowledge.embedder.base import Embedder
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.embedder.openai import OpenAIEmbedder
from loguru import logger

from slidegen.models.embedding_config import EmbeddingConfigBase, EmbeddingProvider
from slidegen.schemas.embedding_config import EmbeddingConfigTest, EmbeddingConfigTestResult


class EmbeddingFactory:
    """Embedding factory class, support creating different provider embedding instances"""

    @staticmethod
    def create_embedder(config: EmbeddingConfigBase | EmbeddingConfigTest) -> Embedder:
        """Create embedding instance based on configuration"""
        try:
            provider = config.provider
            model_id = config.model_id
            api_key = config.api_key
            base_url = config.base_url
            dimensions = getattr(config, "dimensions", None)
            extra_params = getattr(config, "extra_params", {}) or {}

            embedder_params: dict[str, Any] = {
                "id": model_id,
            }

            if api_key:
                embedder_params["api_key"] = api_key

            if dimensions:
                embedder_params["dimensions"] = dimensions

            embedder_params.update(extra_params)

            # Create instance based on different providers
            if provider == EmbeddingProvider.OPENAI:
                if base_url:
                    embedder_params["base_url"] = base_url
                return OpenAIEmbedder(**embedder_params)

            elif provider == EmbeddingProvider.AZURE_OPENAI:
                if base_url:
                    embedder_params["azure_endpoint"] = base_url
                if "azure_deployment" in extra_params:
                    embedder_params["azure_deployment"] = extra_params["azure_deployment"]
                if "api_version" in extra_params:
                    embedder_params["api_version"] = extra_params["api_version"]
                return AzureOpenAIEmbedder(**embedder_params)

            elif provider == EmbeddingProvider.OLLAMA:
                if base_url:
                    embedder_params["host"] = base_url
                # Ollama doesn't need API key
                embedder_params.pop("api_key", None)
                return OllamaEmbedder(**embedder_params)

            elif provider == EmbeddingProvider.CUSTOM:
                # Custom provider, using OpenAI compatible interface
                if base_url:
                    embedder_params["base_url"] = base_url
                return OpenAIEmbedder(**embedder_params)

            else:
                raise ValueError(f"Unsupported embedding provider: {provider}")

        except Exception as e:
            logger.exception(f"Failed to create embedding instance: {str(e)}")
            raise

    @staticmethod
    async def test_embedding_config(config: EmbeddingConfigTest) -> EmbeddingConfigTestResult:
        """Test if the embedding configuration is valid"""
        start_time = time.time()

        try:
            # Create embedding instance
            embedder = EmbeddingFactory.create_embedder(config)

            test_text = config.test_text or "This is a test sentence for embedding."

            # Get embedding
            embedding = embedder.get_embedding(test_text)
            latency = time.time() - start_time

            # Check embedding dimension
            if isinstance(embedding, list):
                embedding_dimension = len(embedding)
            else:
                embedding_dimension = None

            return EmbeddingConfigTestResult(
                success=True, embedding_dimension=embedding_dimension, latency=latency
            )

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            logger.warning(f"Embedding configuration test failed: {error_msg}")

            return EmbeddingConfigTestResult(success=False, error=error_msg, latency=latency)

    @staticmethod
    def validate_config(config: EmbeddingConfigBase | EmbeddingConfigTest) -> tuple[bool, str | None]:
        """Validate the basic parameters of the embedding configuration"""
        try:
            provider = config.provider
            model_id = config.model_id
            api_key = config.api_key
            base_url = config.base_url

            # Check required parameters
            if not model_id:
                return False, "Model ID cannot be empty"

            # Validate specific parameters based on provider
            if provider == EmbeddingProvider.OPENAI:
                if not api_key:
                    return False, "OpenAI needs API key"

            elif provider == EmbeddingProvider.AZURE_OPENAI:
                if not api_key:
                    return False, "Azure OpenAI needs API key"
                if not base_url:
                    return False, "Azure OpenAI needs Azure endpoint URL"

            elif provider == EmbeddingProvider.OLLAMA:
                if not base_url:
                    return False, "Ollama needs server address"

            elif provider == EmbeddingProvider.CUSTOM:
                if not api_key:
                    return False, "Custom provider needs API key"
                if not base_url:
                    return False, "Custom provider needs base URL"

            return True, None

        except Exception as e:
            return False, f"Configuration validation failed: {e!s}"
