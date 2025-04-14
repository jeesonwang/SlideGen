import contextvars
from typing import Any

from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

_request: contextvars.ContextVar[Request | None] = contextvars.ContextVar("request", default=None)
_user_id: contextvars.ContextVar[int | str | None] = contextvars.ContextVar("user_id", default=None)
_role_ids: contextvars.ContextVar[list[int] | None] = contextvars.ContextVar("role_ids", default=None)
_user: contextvars.ContextVar[Any | BaseModel | None] = contextvars.ContextVar("user", default=None)
_session: contextvars.ContextVar[AsyncSession | None] = contextvars.ContextVar("session", default=None)
_session_sync: contextvars.ContextVar[Session | None] = contextvars.ContextVar("session_sync", default=None)
_extra_data: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar("extra_data", default=None)
_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("trace_id", default=None)


class ContextVarsManager:
    _support_keys = ("request", "user_id", "role_ids", "user", "extra_data", "session", "trace_id", "session_sync")

    @property
    def request(self) -> Request | None:
        return _request.get()

    @request.setter
    def request(self, value: Request) -> None:
        _request.set(value)

    @property
    def user_id(self) -> int | str | None:
        return _user_id.get()

    @user_id.setter
    def user_id(self, value: int | str | None) -> None:
        _user_id.set(value)

    @property
    def role_ids(self) -> list[int] | None:
        return _role_ids.get()

    @role_ids.setter
    def role_ids(self, value: list[int] | None) -> None:
        _role_ids.set(value)

    @property
    def user(self) -> Any | BaseModel:
        return _user.get()

    @user.setter
    def user(self, value: Any | BaseModel) -> None:
        _user.set(value)

    @property
    def extra_data(self) -> dict[str, Any] | None:
        return _extra_data.get()

    @extra_data.setter
    def extra_data(self, value: dict[str, Any]) -> None:
        _extra_data.set(value)

    @property
    def trace_id(self) -> str | None:
        return _trace_id.get()

    @trace_id.setter
    def trace_id(self, value: str) -> None:
        _trace_id.set(value)

    @property
    def session(self) -> AsyncSession | None:
        return _session.get()

    @session.setter
    def session(self, value: AsyncSession) -> None:
        _session.set(value)

    @property
    def session_sync(self) -> Session | None:
        return _session_sync.get()

    @session_sync.setter
    def session_sync(self, value: Session) -> None:
        _session_sync.set(value)

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self._support_keys:
            raise ValueError(f"Invalid key {name}, supported keys: {'、'.join(self._support_keys)}")
        return object.__setattr__(self, name, value)


g = ContextVarsManager()
