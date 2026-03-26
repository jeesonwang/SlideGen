from unittest.mock import AsyncMock, Mock, patch

import pytest

from slidegen.schemas.embedding_config import EmbeddingConfigTest, EmbeddingModelsFetchRequest
from slidegen.services.factories.embedding_factory import EmbeddingFactory


@pytest.mark.asyncio
async def test_test_embedding_config_returns_failure_for_empty_embedding() -> None:
    config = EmbeddingConfigTest(
        provider="openai",
        model_id="text-embedding-3-small",
        api_key="invalid-key",
    )
    mock_embedder = AsyncMock()
    mock_embedder.async_get_embedding.return_value = []

    with patch.object(EmbeddingFactory, "create_embedder", return_value=mock_embedder):
        result = await EmbeddingFactory.test_embedding_config(config)

    assert result.success is False
    assert result.embedding_dimension is None
    assert result.error == "Embedding request returned empty result"


@pytest.mark.asyncio
async def test_fetch_available_models_maps_openai_compatible_payload() -> None:
    config = EmbeddingModelsFetchRequest(
        provider="custom",
        api_key="test-key",
        base_url="https://example.com/v1",
    )

    with patch.object(
        EmbeddingFactory,
        "_request_json",
        new=AsyncMock(return_value={
            "data": [
                {"id": "text-embedding-3-small", "name": "Text Embedding 3 Small", "dimensions": 1536},
                {"id": "custom-embedding"},
            ]
        }),
    ) as request_json:
        result = await EmbeddingFactory.fetch_available_models(config)

    request_json.assert_called_once()
    assert result.provider == "custom"
    assert result.models == [
        {"model_id": "text-embedding-3-small", "name": "Text Embedding 3 Small", "dimensions": 1536},
        {"model_id": "custom-embedding", "name": "custom-embedding", "dimensions": None},
    ]


@pytest.mark.asyncio
async def test_request_json_uses_httpx_async_client() -> None:
    mock_response = Mock()
    mock_response.json.return_value = {"data": [{"id": "demo-embedding"}]}
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("slidegen.services.factories.base_factory.httpx.AsyncClient", return_value=mock_client) as async_client:
        result = await EmbeddingFactory._request_json(
            "https://example.com/models",
            {"Authorization": "Bearer test"},
        )

    async_client.assert_called_once()
    mock_client.get.assert_awaited_once_with(
        "https://example.com/models",
        headers={"Authorization": "Bearer test"},
    )
    mock_response.raise_for_status.assert_called_once()
    assert result == {"data": [{"id": "demo-embedding"}]}
