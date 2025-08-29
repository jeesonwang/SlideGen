from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from anyio import CapacityLimiter
from anyio.lowlevel import RunVar
from fastapi import FastAPI

from slidegen.api.main import api_router
from slidegen.core import settings
from slidegen.core.log import init_log
from slidegen.core.middleware import register_middleware

init_log()
app_configs: dict[str, Any] = {}
if not settings.SHOW_DOCS:
    app_configs["docs_url"] = None
    app_configs["redoc_url"] = None
    app_configs["openapi_url"] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    RunVar("_default_thread_limiter").set(CapacityLimiter(settings.SYNC_THREAD_COUNT))  # type: ignore
    yield


app = FastAPI(title=settings.PROJECT_NAME, **app_configs, lifespan=lifespan)
register_middleware(app=app)
app.include_router(api_router)
