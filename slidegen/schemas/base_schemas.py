from collections.abc import Callable, Iterator
from typing import Annotated, Any

from pydantic import BaseModel, Field, WithJsonSchema

from .base import StrDatetime


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


class BaseSchema(BaseModel):
    created_at: StrDatetime | None = Field(default=None, description="创建时间")
    updated_at: StrDatetime | None = Field(default=None, description="更新时间")
    deleted_at: StrDatetime | None = Field(default=None, description="删除时间")


class CommaIntClass(str):
    @classmethod
    def __get_validators__(cls) -> Iterator[Callable[[Any, Any], int]]:
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, _info: Any) -> int:
        if isinstance(v, str) and "," in v:
            v = v.replace(",", "")
        return int(v)


class BulkSchema(BaseSchema):
    ids: list[int] = Field(default_factory=list, description="ID列表")  # noqa


CommaInt = Annotated[
    CommaIntClass,
    WithJsonSchema({"type": "string", "examples": [1, 0, -1]}),
]
