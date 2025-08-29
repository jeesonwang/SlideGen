import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError

from slidegen.exception import MESSAGE, ApiError, ParamCheckErrorCode, UnknownErrorCode


def human_errors(exc: ValidationError) -> str:
    errors = exc.errors()
    for error in errors:
        loc = list(error.get("loc", []))
        loc_len = len(loc)
        msg = error.get("msg") or ""
        error_type = error.get("type")
        if error_type == "json_invalid":
            return msg
        if loc_len == 1:
            text = f"Field {loc[0]} error: {msg}"
            return text
        if loc_len == 2:
            text = "Field "
            if isinstance(loc[1], int):
                text += f"{loc[0]}[{loc[1]}]"
            if isinstance(loc[1], str):
                text += f"`{loc[1]}`"
            text += " error: " + msg
            return text
        if loc_len > 2:
            key_field = None
            if loc[-1] == "[key]":
                key_field = loc.pop()
            text = "Field "
            for ix, field in enumerate(loc[1:]):
                if isinstance(field, str):
                    if ix == 0:
                        text += field
                    else:
                        text += f"['{field}']"
                if isinstance(field, int):
                    text += f"[{field}]"
            if key_field:
                text += f" the value '{loc[-1]}'"
                text += " " + msg
            else:
                text += " error: " + msg
            return text
    return str(errors)


def register_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def custom_exception_handler(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_code,
            content={"message": f"{exc.message}", "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        code = UnknownErrorCode
        return JSONResponse(
            status_code=MESSAGE[code].http_code,
            content={"message": f"{exc}", "code": code},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        try:
            human_err = human_errors(exc)
        except Exception:
            logger.warning("format error fail:")
            return JSONResponse(
                status_code=MESSAGE[ParamCheckErrorCode].http_code,
                content={"message": str(exc), "code": ParamCheckErrorCode},
            )
        return JSONResponse(
            status_code=MESSAGE[ParamCheckErrorCode].http_code,
            content={"message": human_err, "code": ParamCheckErrorCode},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        code = ParamCheckErrorCode
        errors = list(exc.errors())
        model_exc = errors.pop()
        model = model_exc.get("model")
        if not model:
            errors.append(model_exc)
            return JSONResponse(
                status_code=MESSAGE[code].http_code,
                content={"message": f"{exc}", "code": code},
            )
        display_error = ""
        for error in errors:
            for name in error["loc"]:
                field = model.model_dump().get(name)
                if field is not None:
                    display_field_name = name  # if not field.description else field.description
                    display_error += f"{display_field_name} {error['msg']}"
                    break
        return JSONResponse(
            status_code=MESSAGE[code].http_code,
            content={"message": f"{display_error}", "code": code},
        )

    @app.exception_handler(ResponseValidationError)
    async def response_exception_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
        code = ParamCheckErrorCode
        errors = list(exc.errors())
        model_exc = errors.pop()
        model = model_exc.get("model")
        if not model:
            errors.append(model_exc)
            return JSONResponse(
                status_code=MESSAGE[code].http_code,
                content={"message": f"{exc}", "code": code},
            )
        display_error = ""
        for error in errors:
            for name in error["loc"]:
                field = model.model_dump().get(name)
                if field is not None:
                    display_field_name = name  # if not field.description else field.description
                    display_error += f"{display_field_name} {error['msg']}"
                    break
        return JSONResponse(
            status_code=MESSAGE[code].http_code,
            content={"message": f"{display_error}", "code": code},
        )

    @app.middleware("http")
    async def common_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()

        # get request info
        method = request.method
        url = str(request.url.path)
        client_ip = request.client.host  # type: ignore[union-attr]
        client_agent = request.headers.get("user-agent")
        query_params = dict(request.query_params)
        request_body = await request.body()
        # process request
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                f"{method}: {url}, Time Cost: {time.time() - start_time:.4f}s, Query Params: {query_params}, "
                f"Body: {request_body.decode(errors='ignore')[:10]}..., IP: {client_ip}, Agent: {client_agent}."
            )
            raise
        logger.info(
            f"{method}: {url}, Time Cost: {time.time() - start_time:.4f}s, Query Params: {query_params},"
            f" Body: {request_body.decode(errors='ignore')[:10]}..., IP: {client_ip}, Agent: {client_agent}. "
        )
        return response
