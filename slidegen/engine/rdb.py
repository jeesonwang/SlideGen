import contextlib
from typing import AsyncIterator, Any, Annotated
from urllib.parse import quote_plus

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncConnection, async_scoped_session
from sqlalchemy.orm import sessionmaker, scoped_session
from asyncio import current_task

from config.conf import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_CHARSET
from core.context import g


SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset={MYSQL_CHARSET}"
ASYNC_SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset={MYSQL_CHARSET}"

engine = create_engine(
    url=SQLALCHEMY_DATABASE_URL,
    pool_recycle=300,
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,
    echo=False)

session = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))

async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    echo=False,
)

async_session_maker = async_sessionmaker(bind=async_engine, autoflush=False, autocommit=False)
async_session_test = async_scoped_session(async_session_maker, scopefunc=current_task)


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = None):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._session_maker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._session_maker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(ASYNC_SQLALCHEMY_DATABASE_URL, {"echo": False})


async def get_db():
    async with sessionmanager.session() as session:
        g.session = session
        yield session


async_session = Annotated[AsyncSession, Depends(get_db)]


def session_sync_remove(func):
    def wrap(*args, **kwargs):
        if session.is_active:
            session.remove()
        res = func(*args, **kwargs)
        session.remove()
        return res

    return wrap()


def session_remove(func):
    def wrap(*args, **kwargs):
        res = func(*args, **kwargs)
        if async_session_test.is_active:
            async_session_test.remove()
        return res

    return wrap
