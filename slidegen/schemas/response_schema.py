#!/usr/bin/env python3
from datetime import datetime
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, WrapValidator
from pydantic_core.core_schema import ValidationInfo, ValidatorFunctionWrapHandler

T = TypeVar("T", bound=BaseModel)


def maybe_strip_whitespace(v: Any, _handler: ValidatorFunctionWrapHandler, _info: ValidationInfo) -> Any:
    if isinstance(v, datetime):
        return datetime_to_gmt_str(v)
    return v


def datetime_to_gmt_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


model_config = ConfigDict(
    json_encoders={datetime: datetime_to_gmt_str},
    validate_by_name=True,
    validate_by_alias=True,
    validate_assignment=True,
)


class CustomModel(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: datetime_to_gmt_str},
        validate_by_name=True,
        validate_by_alias=True,
        validate_assignment=True,
    )


class ResponseModel(CustomModel, Generic[T]):
    code: int = 0
    data: T
    message: str = "Success"


class ResponseSoftModel(CustomModel, Generic[T]):
    code: int = 0
    data: Annotated[T, WrapValidator(maybe_strip_whitespace)] | None = None
    message: str = "Success"


class ListResponseModel(CustomModel, Generic[T]):
    per_page: int
    page: int
    pages: int
    total: int
    items: list[T]


class ResponseListModel(CustomModel, Generic[T]):
    code: int = 0
    data: ListResponseModel[T]
    message: str = "Success"


class ResponseListSoftModel(CustomModel, Generic[T]):
    code: int = 0
    data: Annotated[ListResponseModel[T], WrapValidator(maybe_strip_whitespace)] | None = None
    message: str = "Success"
