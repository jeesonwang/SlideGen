from fastapi import FastAPI
from anyio.lowlevel import RunVar
from anyio import CapacityLimiter

from config.conf import SYNC_THREAD_COUNT


def startup():
    RunVar("_default_thread_limiter").set(CapacityLimiter(SYNC_THREAD_COUNT))

def register_startup(app: FastAPI):
    app.on_event("startup")(startup)
