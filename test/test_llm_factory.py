import asyncio
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from agno.models.response import ModelResponse

from slidegen.schemas.llm_config import LLMConfigTest, LLMModelsFetchRequest

llm_factory_spec = spec_from_file_location(
    "test_llm_factory_module",
    Path(__file__).resolve().parents[1] / "slidegen/services/factories/llm_factory.py",
)
assert llm_factory_spec is not None and llm_factory_spec.loader is not None
llm_factory_module = module_from_spec(llm_factory_spec)
llm_factory_spec.loader.exec_module(llm_factory_module)
LLMFactory = llm_factory_module.LLMFactory


def test_test_llm_config_uses_response_api() -> None:
    config = LLMConfigTest(
        provider="custom",
        model_id="demo-model",
        api_key="test-key",
        base_url="https://example.com/v1",
        test_prompt="Ping",
    )
    mock_llm = Mock()
    mock_llm.response.return_value = ModelResponse(content="Pong")
    mock_llm.invoke.side_effect = AssertionError("test_llm_config should use response() instead of invoke()")

    with patch.object(LLMFactory, "create_llm", return_value=mock_llm):
        result = asyncio.run(LLMFactory.test_llm_config(config))

    mock_llm.response.assert_called_once()
    assert result.success is True
    assert result.response == "Pong"


def test_fetch_available_models_maps_openai_compatible_payload() -> None:
    config = LLMModelsFetchRequest(
        provider="custom",
        api_key="test-key",
        base_url="https://example.com/v1",
    )

    with patch.object(
        LLMFactory,
        "_request_json",
        new=AsyncMock(
            return_value={
                "data": [
                    {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
                    {"id": "minimax/minimax-m1"},
                ]
            }
        ),
    ) as request_json:
        result = asyncio.run(LLMFactory.fetch_available_models(config))

    request_json.assert_called_once()
    assert result.provider == "custom"
    assert result.models == [
        {"model_id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
        {"model_id": "minimax/minimax-m1", "name": "minimax/minimax-m1"},
    ]


def test_request_json_uses_httpx_async_client() -> None:
    mock_response = Mock()
    mock_response.json.return_value = {"data": [{"id": "demo-model"}]}
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch.object(llm_factory_module.httpx, "AsyncClient", return_value=mock_client) as async_client:
        result = asyncio.run(LLMFactory._request_json("https://example.com/models", {"Authorization": "Bearer test"}))

    async_client.assert_called_once()
    mock_client.get.assert_awaited_once_with("https://example.com/models", headers={"Authorization": "Bearer test"})
    mock_response.raise_for_status.assert_called_once()
    assert result == {"data": [{"id": "demo-model"}]}
