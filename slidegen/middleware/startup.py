from anyio import CapacityLimiter
from anyio.lowlevel import RunVar
from fastapi import FastAPI

from slidegen.config.conf import settings


def startup() -> None:
    RunVar("_default_thread_limiter").set(CapacityLimiter(settings.SYNC_THREAD_COUNT))  # type: ignore


def register_startup(app: FastAPI) -> None:
    app.on_event("startup")(startup)
