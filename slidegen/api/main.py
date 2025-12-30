from fastapi import APIRouter

from slidegen.api.routers import embedding_config, file_upload, llm_config, login, slidegen, user

api_router = APIRouter()

api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(login.router, prefix="/login", tags=["Login"])
api_router.include_router(llm_config.router, prefix="/llm-config", tags=["LLM Config"])
api_router.include_router(embedding_config.router, prefix="/embedding-config", tags=["Embedding Config"])
api_router.include_router(slidegen.router, prefix="/slidegen", tags=["SlideGen"])
api_router.include_router(file_upload.router, prefix="/files", tags=["file management"])
