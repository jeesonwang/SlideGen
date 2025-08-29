from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from slidegen.api.main import api_router
from slidegen.common import logger_init
from slidegen.config import settings
from slidegen.middleware.exception import register_exception_handler


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Tables be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # async with async_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    # await async_engine.dispose()


def create_app() -> FastAPI:
    """
    configure and create the FastAPI application instance.
    """
    logger_init()

    app_configs: dict[str, Any] = {}
    if not settings.SHOW_DOCS:
        app_configs["docs_url"] = None
        app_configs["redoc_url"] = None
        app_configs["openapi_url"] = None

    app = FastAPI(
        title=settings.PROJECT_NAME,
        generate_unique_id_function=custom_generate_unique_id,
        **app_configs,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handler(app)
    app.include_router(api_router, prefix=settings.API_V1_STR)
    # Mount the data files to serve the file viewer
    app.mount(
        "/api/files/data",
        StaticFiles(directory="data", check_dir=False),
    )
    return app
