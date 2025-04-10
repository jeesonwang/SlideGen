from datetime import datetime
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, ConfigDict, WrapValidator
from pydantic_core.core_schema import ValidationInfo, ValidatorFunctionWrapHandler

T = TypeVar("T", bound=BaseModel)


def maybe_strip_whitespace(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> int:
    if isinstance(v, datetime):
        return datetime_to_gmt_str(v)
    return v


def datetime_to_gmt_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


model_config = ConfigDict(
    json_encoders={datetime: datetime_to_gmt_str},
    populate_by_name=True,
)


class CustomModel(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: datetime_to_gmt_str},
        populate_by_name=True,
    )


def Res(data_model: T, validate: bool = False):
    class ResponseModel(CustomModel):
        model_config = model_config
        code: int = 0
        data: T
        message: str = "Success"

    class ResponseSoftModel(CustomModel):
        model_config = model_config
        code: int = 0
        data: Annotated[T, WrapValidator(maybe_strip_whitespace)] = None
        message: str = "Success"

    if validate:
        return ResponseModel
    else:
        return ResponseSoftModel


def ListRes(data_model, validate: bool = False):
    class ListResponseModel(CustomModel):
        model_config = model_config
        per_page: int
        page: int
        pages: int
        total: int
        items: list[T]

    class ResponseModel(CustomModel):
        model_config = model_config
        code: int = 0
        data: ListResponseModel
        message: str = "Success"

    class ResponseSoftModel(CustomModel):
        model_config = model_config
        code: int = 0
        data: Annotated[ListResponseModel, WrapValidator(maybe_strip_whitespace)] = None
        message: str = "Success"

    if validate:
        return ResponseModel
    else:
        return ResponseSoftModel


def PagerRes(data_model: T, validate: bool = False):
    class ListResponseModel(CustomModel):
        model_config = model_config
        per_page: int
        page: int
        pages: int
        total: int
        items: list[T]

    class ResponseModel(CustomModel):
        model_config = model_config
        code: int = 0
        data: ListResponseModel
        message: str = "Success"

    class ResponseSoftModel(CustomModel):
        model_config = model_config
        code: int = 0
        data: Annotated[ListResponseModel, WrapValidator(maybe_strip_whitespace)] = None
        message: str = "Success"

    if validate:
        return ResponseModel
    else:
        return ResponseSoftModel
