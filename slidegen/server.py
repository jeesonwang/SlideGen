from fastapi import FastAPI


from common.log import init as logger_init
from middleware import register_middleware
from view import register_routes
from config.conf import SHOW_DOCS

logger_init()
app_configs = {}
if not SHOW_DOCS:
    app_configs["docs_url"] = None
    app_configs["redoc_url"] = None
    app_configs["openapi_url"] = None

app = FastAPI(**app_configs)
register_middleware(app=app)
register_routes(app=app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=10003, reload=True)
