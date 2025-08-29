from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from slidegen.config import settings
from slidegen.models.base import Base


class _DatabaseSettings:
    """Pulled from environment once at import-time."""

    SYNC_DATABASE_URL: str = settings.SQLALCHEMY_DATABASE_URI.encoded_string()
    ASYNC_DATABASE_URL: str = settings.SQLALCHEMY_ASYNC_DATABASE_URI.encoded_string()
    DB_ECHO: bool = settings.DB_ECHO
    DB_CONNECT_ARGS: dict[str, Any] = {}


database_settings = _DatabaseSettings()


@lru_cache(maxsize=1)
def _make_sync_engine() -> Engine:
    """Create (or return) the global synchronous Engine."""
    engine = create_engine(
        database_settings.SYNC_DATABASE_URL,
        echo=database_settings.DB_ECHO,
        pool_pre_ping=True,
        connect_args=database_settings.DB_CONNECT_ARGS,
        future=True,
        pool_size=10,
        max_overflow=20,
    )
    return engine


@lru_cache(maxsize=1)
def _make_async_engine() -> AsyncEngine:
    """Create (or return) the global asynchronous Engine."""
    engine = create_async_engine(
        database_settings.ASYNC_DATABASE_URL,
        echo=database_settings.DB_ECHO,
        pool_pre_ping=True,
        connect_args=database_settings.DB_CONNECT_ARGS,
        future=True,
        pool_size=10,
        max_overflow=20,
    )
    return engine


# Session factories
sync_engine: Engine = _make_sync_engine()
async_engine: AsyncEngine = _make_async_engine()

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


def get_sync_db_session() -> Generator[Session, None, None]:
    """
    Yield a *transactional* synchronous ``Session``.

    Commits if no exception was raised, otherwise rolls back. Always closes.
    Useful for CLI scripts or rare sync paths.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_models(Base: Base) -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
