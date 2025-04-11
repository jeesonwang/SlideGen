from typing import Any

from fastapi import FastAPI

from slidegen.common.log import init as logger_init
from slidegen.config.conf import settings
from slidegen.middleware import register_middleware
from slidegen.view import register_routes

logger_init()
app_configs: dict[str, Any] = {}
if not settings.SHOW_DOCS:
    app_configs["docs_url"] = None
    app_configs["redoc_url"] = None
    app_configs["openapi_url"] = None

app = FastAPI(title=settings.PROJECT_NAME, **app_configs)
register_middleware(app=app)
register_routes(app=app)
