import contextvars
from typing import Union, Any

from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

_request = contextvars.ContextVar("request", default=None)
_user_id = contextvars.ContextVar("user_id", default=None)
_role_ids = contextvars.ContextVar("role_ids", default=None)
_user = contextvars.ContextVar("user", default=None)
_session = contextvars.ContextVar("session", default=None)
_session_sync = contextvars.ContextVar("session_sync", default=None)
_extra_data = contextvars.ContextVar("extra_data", default=None)
_trace_id = contextvars.ContextVar("trace_id", default=None)


class ContextVarsManager:
    _support_keys = ("request", "user_id", "role_ids", "user", "extra_data", "session", "trace_id", "session_sync")

    @property
    def request(self) -> Request:
        return _request.get()

    @request.setter
    def request(self, value: Request):
        _request.set(value)

    @property
    def user_id(self) -> Union[int, str, None]:
        return _user_id.get()

    @user_id.setter
    def user_id(self, value: Union[int, str, None]):
        _user_id.set(value)

    @property
    def role_ids(self) -> Union[list[int], None]:
        return _role_ids.get()

    @role_ids.setter
    def role_ids(self, value: Union[list[int], None]):
        _role_ids.set(value)

    @property
    def user(self) -> Union[Any, BaseModel]:
        return _user.get()

    @user.setter
    def user(self, value: Union[Any, BaseModel]):
        _user.set(value)

    @property
    def extra_data(self) -> dict:
        return _extra_data.get()

    @extra_data.setter
    def extra_data(self, value: dict):
        _extra_data.set(value)

    @property
    def trace_id(self) -> str:
        return _trace_id.get()

    @trace_id.setter
    def trace_id(self, value: str):
        _trace_id.set(value)

    @property
    def session(self) -> AsyncSession:
        return _session.get()

    @session.setter
    def session(self, value: AsyncSession):
        _session.set(value)

    @property
    def session_sync(self) -> Session:
        return _session_sync.get()

    @session_sync.setter
    def session_sync(self, value: Session):
        _session_sync.set(value)

    def __setattr__(self, name: str, value: Any):
        if name not in self._support_keys:
            raise ValueError(f"Invalid key {name}, supported keys: {'、'.join(self._support_keys)}")
        return object.__setattr__(self, name, value)


g = ContextVarsManager()

