import contextlib
from typing import Annotated, AsyncIterator, Iterator
from urllib.parse import quote_plus

from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session

from config.conf import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DB,
    MYSQL_CHARSET,
    DB_TYPE,
)
from core import g

if DB_TYPE == "MYSQL":
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset={MYSQL_CHARSET}"
    ASYNC_SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset={MYSQL_CHARSET}"
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
else:
    raise RuntimeError(f"Unsupported database: {DB_TYPE}")

print(f"DB_TYPE={DB_TYPE}, Connecting to database url={SQLALCHEMY_DATABASE_URL}")


class DatabaseSessionManager:
    def __init__(self):
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
            await g.session.rollback()
            raise
        finally:
            await g.session.close()

    @contextlib.asynccontextmanager
    async def session_sync(self) -> AsyncIterator[Session]:
        if self._session_maker_sync is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = await run_in_threadpool(lambda: self._session_maker_sync())
        try:
            yield session
        except Exception:
            await run_in_threadpool(lambda: g.session_sync.rollback())
            raise
        finally:
            await run_in_threadpool(lambda: g.session_sync.close())


sessionmanager = DatabaseSessionManager()


async def get_db():
    async with sessionmanager.session() as session:
        g.session = session
        yield session


async def get_db_sync():
    async with sessionmanager.session_sync() as session:
        g.session_sync = session
        yield session


def load_session_context(func):
    def wrapper(*args, **kwargs):
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


session_type = Annotated[AsyncSession, Depends(get_db)]
session_type_sync = Annotated[AsyncSession, Depends(get_db_sync)]
