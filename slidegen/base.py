from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from slidegen.api.main import api_router
from slidegen.core import logger_init, settings
from slidegen.init_data import init_app_data
from slidegen.middleware import register_exception_handler


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize application data (create first superuser, etc.)
    await init_app_data()

    # Ensure output directory exists
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
