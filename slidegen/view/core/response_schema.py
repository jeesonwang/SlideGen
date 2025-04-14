from datetime import datetime
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, ConfigDict, WrapValidator
from pydantic_core.core_schema import ValidationInfo, ValidatorFunctionWrapHandler

T = TypeVar("T", bound=BaseModel)


def maybe_strip_whitespace(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> Any:
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


class ResponseModel(CustomModel):
    model_config = model_config
    code: int = 0
    data: type[BaseModel]
    message: str = "Success"


class ResponseSoftModel(CustomModel):
    model_config = model_config
    code: int = 0
    data: Annotated[type[BaseModel] | None, WrapValidator(maybe_strip_whitespace)] = None
    message: str = "Success"


# List response model
class ListResponseModel(CustomModel):
    model_config = model_config
    per_page: int
    page: int
    pages: int
    total: int
    items: list[type[BaseModel]]


class ListResponseDataModel(CustomModel):
    model_config = model_config
    code: int = 0
    data: ListResponseModel
    message: str = "Success"


class ListResponseSoftDataModel(CustomModel):
    model_config = model_config
    code: int = 0
    data: Annotated[ListResponseModel | None, WrapValidator(maybe_strip_whitespace)] = None
    message: str = "Success"


# Page response model
class PageResponseModel(CustomModel):
    model_config = model_config
    per_page: int
    page: int
    pages: int
    total: int
    items: list[type[BaseModel]]


class PageResponseDataModel(CustomModel):
    model_config = model_config
    code: int = 0
    data: PageResponseModel
    message: str = "Success"


class PageResponseSoftDataModel(CustomModel):
    model_config = model_config
    code: int = 0
    data: Annotated[PageResponseModel | None, WrapValidator(maybe_strip_whitespace)] = None
    message: str = "Success"
