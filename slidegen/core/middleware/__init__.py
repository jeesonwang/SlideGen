from fastapi import FastAPI

from .cors import register_cors
from .exception import register_exception_handler


def register_middleware(app: FastAPI) -> None:
    register_cors(app)
    register_exception_handler(app)
