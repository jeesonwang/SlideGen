from datetime import datetime
from typing import Annotated, Any

from pydantic import ValidationInfo, ValidatorFunctionWrapHandler, WrapValidator


def datetime_to_gmt_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def datetime_to_gmt_str_validator(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> Any:
    if isinstance(v, datetime):
        return datetime_to_gmt_str(v)
    return v


StrDatetime = Annotated[Any, WrapValidator(datetime_to_gmt_str_validator)]
