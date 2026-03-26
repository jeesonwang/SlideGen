import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from slidegen.api.deps import get_current_user
from slidegen.api.routers.embedding_config import router
from slidegen.core.database import get_db_session
from slidegen.models.embedding_config import EmbeddingConfigModel


def test_create_embedding_config_succeeds_without_user_id_in_request_body() -> None:
    current_user = SimpleNamespace(id=uuid.uuid4())
    persisted_config: SimpleNamespace | None = None

    async def override_get_current_user() -> SimpleNamespace:
        return current_user

    async def override_get_db_session() -> SimpleNamespace:
        async def refresh(config: SimpleNamespace) -> None:
            nonlocal persisted_config
            persisted_config = config

        return SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))),
            add=AsyncMock(),
            commit=AsyncMock(),
            refresh=AsyncMock(side_effect=refresh),
        )

    app = FastAPI()
    app.include_router(router, prefix="/embedding-config")
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db_session] = override_get_db_session

    client = TestClient(app)

    response = client.post(
        "/embedding-config/",
        json={
            "name": "demo embedding",
            "provider": "openai",
            "model_id": "text-embedding-3-small",
            "api_key": "sk-test-1234",
            "is_default": False,
        },
    )

    assert response.status_code == 200
    assert persisted_config is not None
    body = response.json()
    assert body["name"] == "demo embedding"
    assert body["provider"] == "openai"
    assert body["model_id"] == "text-embedding-3-small"
    assert body["user_id"] == str(current_user.id)
    assert body["api_key"] == "***1234"


def test_test_embedding_config_uses_stored_api_key_when_request_contains_masked_value() -> None:
    current_user = SimpleNamespace(id=uuid.uuid4())
    config_id = uuid.uuid4()
    stored_config = EmbeddingConfigModel.model_validate(
        {
            "id": config_id,
            "user_id": current_user.id,
            "name": "demo embedding",
            "provider": "openai",
            "model_id": "text-embedding-3-small",
            "api_key": "sk-live-secret",
            "base_url": "https://api.openai.com/v1",
            "dimensions": 1536,
            "is_active": True,
            "is_default": False,
        }
    )

    async def override_get_current_user() -> SimpleNamespace:
        return current_user

    async def override_get_db_session() -> SimpleNamespace:
        return SimpleNamespace(get=AsyncMock(return_value=stored_config))

    app = FastAPI()
    app.include_router(router, prefix="/embedding-config")
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db_session] = override_get_db_session

    client = TestClient(app)

    with patch(
        "slidegen.api.routers.embedding_config.EmbeddingFactory.test_embedding_config",
        new=AsyncMock(),
    ) as test_embedding_config:
        test_embedding_config.return_value = {
            "success": True,
            "embedding_dimension": 1536,
            "latency": 0.1,
        }

        response = client.post(
            "/embedding-config/test",
            json={
                "config_id": str(config_id),
                "provider": "openai",
                "model_id": "text-embedding-3-small",
                "api_key": "***cret",
                "base_url": "https://api.openai.com/v1",
                "test_text": "ping",
            },
        )

    assert response.status_code == 200
    forwarded_config = test_embedding_config.await_args.args[0]
    assert forwarded_config.api_key == "sk-live-secret"
