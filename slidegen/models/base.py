import json
from collections.abc import Callable
from typing import Any

from sqlalchemy import Column, DateTime, Integer, SmallInteger, Text
from sqlalchemy.types import TypeDecorator

from slidegen.contexts import g
from slidegen.core.log.patch.json_decoder import CustomJSONEncoder
from slidegen.util.time import now_datetime

try:
    # sqlalchemy1.4+
    from sqlalchemy.orm import declarative_base
except ImportError:
    # sqlalchemy1.3
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class JsonText(TypeDecorator[Any]):
    impl = Text  # 基础类型
    cache_ok = True  # 是否使用Sqlalchemy缓存

    def process_bind_param(self, value: Any | None, dialect: Any) -> Any | None:
        if value is not None:
            value = json.dumps(value, ensure_ascii=False, cls=CustomJSONEncoder)
        return value

    def process_result_value(self, value: Any | None, dialect: Any) -> Any | None:
        if value is not None:
            value = json.loads(value)
        return value


class Boolean(TypeDecorator[bool]):
    impl = SmallInteger  # 基础类型
    cache_ok = True  # 是否使用Sqlalchemy缓存

    def process_bind_param(self, value: bool | None, dialect: Any) -> int | None:
        if value is not None:
            value = int(value)  # type: ignore
        return value

    def process_result_value(self, value: int | None, dialect: Any) -> bool | None:
        if value is not None:
            value = bool(value)
        return value


def same_as(column_name: str) -> Callable[[Any], Any]:
    def default_function(context: Any) -> Any:
        return context.get_current_parameters()[column_name]

    return default_function


def get_attr_from_g(name: str, default: Any = None, raise_exception: bool = False) -> Callable[[], Any]:
    """从g对象中获取默认参数"""

    def getter() -> Any:
        try:
            if not hasattr(g, name):
                if raise_exception:
                    raise AttributeError("flask g has not attribute {name}")
                return default
            return getattr(g, name)
        except RuntimeError:
            return default

    return getter


class BaseModel(Base):  # type: ignore
    """基类表模板"""

    __abstract__ = True

    create_user_id = Column(
        Integer, nullable=False, index=True, default=get_attr_from_g("user_id", default=0), comment="创建用户ID"
    )
    create_time = Column(DateTime(timezone=True), nullable=False, default=now_datetime, index=True, comment="创建时间")
    update_user_id = Column(
        Integer,
        nullable=False,
        default=get_attr_from_g("user_id", default=0),
        onupdate=get_attr_from_g("user_id", default=0),
        comment="修改用户ID",
    )
    update_time = Column(
        DateTime(timezone=True), nullable=False, default=now_datetime, onupdate=now_datetime, comment="修改时间"
    )
    is_delete = Column(Boolean, nullable=False, default=False, comment="是否已删除")

    def to_dict(self, include: list[str] | None = None, exclude: list[str] | None = None) -> dict[str, Any]:
        exclude = [] if exclude is not None else exclude
        include_mapper: dict[str, str] = {}
        if include is not None:
            for key in include:
                if ":" in key:
                    rename_key = key.split(":", maxsplit=1)
                    include_mapper.setdefault(*rename_key)
                else:
                    include_mapper[key] = key

        res = {}
        for c in self.__table__.columns:
            if include is not None and c.name not in include_mapper:
                continue
            if exclude is not None and c.name in exclude:
                continue
            res[include_mapper.get(c.name, c.name)] = getattr(self, c.name, None)
        return res
