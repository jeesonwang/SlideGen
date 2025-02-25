import time

from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from core.context import g
from exception import ApiError, UnknownErrorCode, ParamCheckErrorCode, MESSAGE


def register_exception_handler(app: FastAPI):
    @app.exception_handler(ApiError)
    async def custom_exception_handler(request: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.http_code,
            content={"message": f"{exc.message}", "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc):
        code = UnknownErrorCode
        return JSONResponse(
            status_code=MESSAGE[code]["http_code"],
            content={"message": f"{exc}", "code": code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        code = ParamCheckErrorCode
        errors = exc.errors()
        model_exc = errors.pop()
        model: BaseModel = model_exc.get("model")
        if not model:
            errors.append(model_exc)
            return JSONResponse(
                status_code=MESSAGE[code]["http_code"],
                content={"message": f"{exc}", "code": code},
            )
        display_error = ""
        for error in errors:
            for name in error["loc"]:
                field = model.model_fields.get(name)
                if field is not None:
                    display_field_name = name  # if not field.description else field.description
                    display_error += f"{display_field_name} {error['msg']}"
                    break
        return JSONResponse(
            status_code=MESSAGE[code]["http_code"],
            content={"message": f"{display_error}", "code": code},
        )

    @app.exception_handler(ResponseValidationError)
    async def response_exception_handler(request, exc):
        code = UnknownErrorCode
        errors = exc.errors()
        model_exc = errors.pop()
        model: BaseModel = model_exc.get("model")
        if not model:
            errors.append(model_exc)
            return JSONResponse(
                status_code=MESSAGE[code]["http_code"],
                content={"message": f"{exc}", "code": code},
            )
        display_error = ""
        for error in errors:
            for name in error["loc"]:
                field = model.model_fields.get(name)
                if field is not None:
                    display_field_name = name  # if not field.description else field.description
                    display_error += f"{display_field_name} {error['msg']}"
                    break
        return JSONResponse(
            status_code=MESSAGE[code]["http_code"],
            content={"message": f"{display_error}", "code": code},
        )

    @app.middleware("http")
    async def common_requests(request: Request, call_next):
        # 记录请求开始时间
        start_time = time.time()

        # 获取请求信息
        method = request.method
        url = str(request.url.path)
        client_ip = request.client.host
        client_agent = request.headers.get("user-agent")
        query_params = dict(request.query_params)
        request_body = await request.body()
        g.request = request
        # 处理请求
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(f"接口异常{url=}")
            raise

        # 计算请求处理时间
        duration = time.time() - start_time

        # 记录日志
        try:
            logger.info(
                f"{method}: {url}, 用时: {duration:.4f}s, Query Params: {query_params},"
                f" Body: {request_body.decode()} IP: {client_ip}, Agent: {client_agent}. ")
            # from db.backends.mysql import session
            # session.remove()
        except Exception:
            logger.exception("日志记录异常")
        return response
