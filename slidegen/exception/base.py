from typing import Any

from slidegen.contexts import BaseResponse
from slidegen.exception.error_code import MESSAGE, UnknownErrorCode


class ApiError(Exception):
    """
    标准API异常
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
        :param http_code: http状态码
        :param data: 附加数据
        :param args:
        :param kwargs:
        """
        super().__init__(message, *args)

        self.code = code or self.default_code
        self.message = message or MESSAGE[self.code]["message"]
        self.http_code = http_code or MESSAGE[self.code]["http_code"]
        self.data = data

    def __str__(self) -> str:
        return f"""{self.__class__.__name__}(code={self.code}, message={self.message}, http_code={self.http_code})"""

    @property
    def result(self) -> BaseResponse:
        return BaseResponse(code=self.code, message=self.message, status_code=self.http_code)  # type: ignore
