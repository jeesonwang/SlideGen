from typing import Any

from pydantic import BaseModel

from .error_code import MESSAGE, UnknownErrorCode


class BaseResponse(BaseModel):
    code: int
    message: str
    status_code: int


class ApiError(Exception):
    """
    Standard API error
    """

    default_code = UnknownErrorCode

    def __init__(
        self,
        message: str | None = None,
        code: int | None = None,
        http_code: int | None = None,
        data: dict[str, Any] | list[Any] | str | None = None,
        *args: Any,
    ):
        """
        标准API异常构造函数

        :param code: 异常编码
        :param message: 异常信息
        :param http_code: HTTP状态码
        :param args:
        :param kwargs:
        """

        super().__init__(message, *args)

        self.code = code or self.default_code
        self.message = message or MESSAGE[self.code].message
        self.http_code = http_code or MESSAGE[self.code].http_code
        self.data = data

    def __str__(self) -> str:
        return f"""{self.__class__.__name__}(code={self.code}, message={self.message}, http_code={self.http_code})"""

    def result(self) -> BaseResponse:
        return BaseResponse(code=self.code, message=self.message, status_code=self.http_code)
