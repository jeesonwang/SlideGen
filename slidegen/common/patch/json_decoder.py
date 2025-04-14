import decimal
from dataclasses import asdict, is_dataclass
from datetime import date, time, timedelta
from json import JSONEncoder
from typing import Any


class CustomJSONEncoder(JSONEncoder):
    """修改datetime打印格式"""

    def default(self, obj: Any) -> Any:
        try:
            if isinstance(obj, (date, time, timedelta)):
                return str(obj)[:19]
            if isinstance(obj, decimal.Decimal):
                return str(obj)
            if is_dataclass(obj):
                return asdict(obj)  # type: ignore
            iterable = iter(obj)
        except TypeError as err:
            print(err)
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
