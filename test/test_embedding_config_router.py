import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from slidegen.api.deps import get_current_user
from slidegen.api.routers.embedding_config import router
from slidegen.core.database import get_db_session


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
