import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from slidegen.contexts.context import g
from slidegen.exception import MESSAGE, ApiError, ParamCheckErrorCode, UnknownErrorCode


def register_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def custom_exception_handler(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_code,  # type: ignore
            content={"message": f"{exc.message}", "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        code = UnknownErrorCode
        return JSONResponse(
            status_code=MESSAGE[code]["http_code"],  # type: ignore
            content={"message": f"{exc}", "code": code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        code = ParamCheckErrorCode
        errors = exc.errors()
        model_exc = errors.pop()  # type: ignore
        model: BaseModel = model_exc.get("model")
        if not model:
            errors.append(model_exc)  # type: ignore
            return JSONResponse(
                status_code=MESSAGE[code]["http_code"],  # type: ignore
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
            status_code=MESSAGE[code]["http_code"],  # type: ignore
            content={"message": f"{display_error}", "code": code},
        )

    @app.exception_handler(ResponseValidationError)
    async def response_exception_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
        code = UnknownErrorCode
        errors = exc.errors()
        model_exc = errors.pop()  # type: ignore
        model: BaseModel = model_exc.get("model")
        if not model:
            errors.append(model_exc)  # type: ignore
            return JSONResponse(
                status_code=MESSAGE[code]["http_code"],  # type: ignore
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
            status_code=MESSAGE[code]["http_code"],  # type: ignore
            content={"message": f"{display_error}", "code": code},
        )

    @app.middleware("http")
    async def common_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # 记录请求开始时间
        start_time = time.time()

        # 获取请求信息
        method = request.method
        url = str(request.url.path)
        client_ip = request.client.host  # type: ignore
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
                f" Body: {request_body.decode()} IP: {client_ip}, Agent: {client_agent}. "
            )
            # from db.backends.mysql import session
            # session.remove()
        except Exception:
            logger.exception("日志记录异常")
        return response
