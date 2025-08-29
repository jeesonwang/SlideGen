from fastapi import APIRouter

from slidegen.api.demo import sse, websocket
from slidegen.api.routes import auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sse.router, prefix="/demo", tags=["demo"])
api_router.include_router(websocket.router, prefix="/demo", tags=["demo"])
