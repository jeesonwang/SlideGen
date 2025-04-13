from fastapi import FastAPI

from .cors import register_cors
from .exception import register_exception_handler
from .startup import register_startup


def register_middleware(app: FastAPI) -> None:
    register_cors(app)
    register_exception_handler(app)
    register_startup(app)
