from fastapi import FastAPI

from .core import base_router
from .om.healthcheck import HealthCheckView

HealthCheckView(path="/healthcheck", tags=["运维"])


def register_routes(app: FastAPI):
    app.include_router(router=base_router)
