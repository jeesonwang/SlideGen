from typing import Any

from pydantic import BaseModel


class BaseResponse(BaseModel):
    code: int = 0
    status_code: int = 200
    message: str = "request success"
    data: dict[str, Any] | None = {}


class Pager(BaseModel):
    per_page: int
    page: int
    pages: int
    total: int
