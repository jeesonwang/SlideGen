import contextlib
from collections.abc import AsyncIterator, Callable
from typing import Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from slidegen.contexts import g
from slidegen.core import settings

if settings.DB_TYPE == "MYSQL":
    SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
    ASYNC_SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_ASYNC_DATABASE_URI)
    engine_sync = create_engine(
        url=SQLALCHEMY_DATABASE_URL,
        pool_recycle=300,
        pool_size=20,
        max_overflow=15,
        pool_timeout=15,
        echo=False,
    )
    engine = create_async_engine(
        url=ASYNC_SQLALCHEMY_DATABASE_URL,
        pool_recycle=300,
        pool_size=20,
        max_overflow=15,
        pool_timeout=15,
        echo=False,
    )
    session_maker_sync = sessionmaker(bind=engine_sync, autocommit=False, autoflush=False)
    session_maker = async_sessionmaker(bind=engine, autoflush=False, autocommit=False)


class DatabaseSessionManager:
    def __init__(self) -> None:
        self._session_maker = session_maker
        self._engine_sync = engine_sync
        self._session_maker_sync = session_maker_sync

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._session_maker()
        try:
            yield session
        except Exception:
            await g.session.rollback()  # type: ignore
            raise
        finally:
            await g.session.close()  # type: ignore

    @contextlib.asynccontextmanager
    async def session_sync(self) -> AsyncIterator[Session]:
        if self._session_maker_sync is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = await run_in_threadpool(lambda: self._session_maker_sync())
        try:
            yield session
        except Exception:
            await run_in_threadpool(lambda: g.session_sync.rollback())  # type: ignore
            raise
        finally:
            await run_in_threadpool(lambda: g.session_sync.close())  # type: ignore


sessionmanager = DatabaseSessionManager()


async def get_db() -> AsyncIterator[AsyncSession]:
    async with sessionmanager.session() as session:
        g.session = session
        yield session


async def get_db_async() -> AsyncIterator[Session]:
    async with sessionmanager.session_sync() as session:
        g.session_sync = session
        yield session


def load_session_context(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        session = sessionmanager._session_maker_sync()
        g.session_sync = session
        try:
            return func(*args, **kwargs)
        except Exception:
            g.session_sync.rollback()
            raise
        finally:
            g.session_sync.close()

    return wrapper
