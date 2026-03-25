from unittest.mock import AsyncMock, patch

import pytest

from slidegen.schemas.embedding_config import EmbeddingConfigTest
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
