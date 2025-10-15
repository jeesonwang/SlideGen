import time
from typing import Any

from agno.models.anthropic import Claude
from agno.models.azure.openai_chat import AzureOpenAI
from agno.models.base import Model
from agno.models.message import Message
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat as OpenAI
from agno.models.openai import OpenAILike
from agno.models.openrouter import OpenRouter
from loguru import logger

from slidegen.models.llm_config import LLMConfigModel, LLMProvider
from slidegen.schemas.llm_config import LLMConfigTest, LLMConfigTestResult


class LLMFactory:
    """LLM factory class, support creating different provider LLM instances"""

    @staticmethod
    def create_llm(config: LLMConfigModel | LLMConfigTest) -> Model:
        """Create LLM instance based on configuration"""
        try:
            provider = config.provider
            model_id = config.model_id
            api_key = config.api_key
            base_url = config.base_url
            temperature = getattr(config, "temperature", 0.7)
            max_tokens = getattr(config, "max_tokens", None)
            top_p = getattr(config, "top_p", None)
            extra_params = getattr(config, "extra_params", {}) or {}

            llm_params: dict[str, Any] = {
                "id": model_id,
                "temperature": temperature,
            }

            if api_key:
                llm_params["api_key"] = api_key

            if max_tokens:
                llm_params["max_tokens"] = max_tokens

            if top_p:
                llm_params["top_p"] = top_p

            llm_params.update(extra_params)

            # Create instance based on different providers
            if provider == LLMProvider.OPENAI:
                if base_url:
                    llm_params["base_url"] = base_url
                return OpenAI(**llm_params)

            elif provider == LLMProvider.OPENROUTER:
                # OpenRouter uses fixed base_url
                return OpenRouter(**llm_params)

            elif provider == LLMProvider.ANTHROPIC:
                if base_url:
                    llm_params["base_url"] = base_url
                return Claude(**llm_params)

            elif provider == LLMProvider.AZURE_OPENAI:
                if base_url:
                    llm_params["azure_endpoint"] = base_url
                if "azure_deployment" in extra_params:
                    llm_params["azure_deployment"] = extra_params["azure_deployment"]
                if "api_version" in extra_params:
                    llm_params["api_version"] = extra_params["api_version"]
                return AzureOpenAI(**llm_params)

            elif provider == LLMProvider.OLLAMA:
                if base_url:
                    llm_params["host"] = base_url
                # Ollama doesn't need API key
                llm_params.pop("api_key", None)
                return Ollama(**llm_params)

            elif provider == LLMProvider.CUSTOM:
                # Custom provider, using OpenAI compatible interface
                if base_url:
                    llm_params["base_url"] = base_url
                return OpenAILike(**llm_params)

            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

        except Exception as e:
            logger.exception(f"Failed to create LLM instance: {str(e)}")
            raise

    @staticmethod
    async def test_llm_config(config: LLMConfigTest) -> LLMConfigTestResult:
        """Test if the LLM configuration is valid"""
        start_time = time.time()

        try:
            # Create LLM instance
            llm = LLMFactory.create_llm(config)

            test_prompt = config.test_prompt or "Hello, how are you?"
            message = Message(role="user", content=test_prompt)
            response = llm.invoke([message])
            latency = time.time() - start_time

            if hasattr(response, "content"):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            return LLMConfigTestResult(success=True, response=response_text, latency=latency)

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            logger.warning(f"LLM configuration test failed: {error_msg}")

            return LLMConfigTestResult(success=False, error=error_msg, latency=latency)

    @staticmethod
    def validate_config(config: LLMConfigModel | LLMConfigTest) -> tuple[bool, str | None]:
        """Validate the basic parameters of the LLM configuration"""
        try:
            provider = config.provider
            model_id = config.model_id
            api_key = config.api_key
            base_url = config.base_url

            # Check required parameters
            if not model_id:
                return False, "Model ID cannot be empty"

            # Validate specific parameters based on provider
            if provider == LLMProvider.OPENAI:
                if not api_key:
                    return False, "OpenAI needs API key"

            elif provider == LLMProvider.OPENROUTER:
                if not api_key:
                    return False, "OpenRouter needs API key"

            elif provider == LLMProvider.ANTHROPIC:
                if not api_key:
                    return False, "Anthropic needs API key"

            elif provider == LLMProvider.AZURE_OPENAI:
                if not api_key:
                    return False, "Azure OpenAI needs API key"
                if not base_url:
                    return False, "Azure OpenAI needs Azure endpoint URL"

            elif provider == LLMProvider.OLLAMA:
                if not base_url:
                    return False, "Ollama needs server address"

            elif provider == LLMProvider.CUSTOM:
                if not api_key:
                    return False, "Custom provider needs API key"
                if not base_url:
                    return False, "Custom provider needs base URL"

            return True, None

        except Exception as e:
            return False, f"Configuration validation failed: {e!s}"
