"""Подключение к PostgreSQL через SQLAlchemy async.

Единый async-движок и фабрика сессий на весь процесс. Так как задачи Celery
запускаются через `asyncio.run` (новый event loop на задачу), после каждой
задачи движок освобождается через `close_pool()`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.settings import settings


POOL_SIZE = 2
MAX_OVERFLOW = 8
POOL_RECYCLE_SECONDS = 1800
POOL_PRE_PING = True


_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _async_dsn() -> str:
    """Приводит DATABASE_URL к диалекту asyncpg, понятному SQLAlchemy."""

    url = settings.DATABASE_URL

    for prefix in ('postgresql+asyncpg://', 'postgres://', 'postgresql://'):
        if url.startswith(prefix):
            return 'postgresql+asyncpg://' + url[len(prefix):]

    return url


def get_engine() -> AsyncEngine:
    """Возвращает (создавая при первом вызове) общий async-движок."""

    global _engine

    if _engine is None:
        _engine = create_async_engine(
            _async_dsn(),
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_recycle=POOL_RECYCLE_SECONDS,
            pool_pre_ping=POOL_PRE_PING,
            future=True,
            # Таймзона сессии PostgreSQL: без неё now()/func.now() возвращает
            # время в UTC (+00). Здесь включаем зону из настроек приложения.
            connect_args={'server_settings': {'timezone': settings.TIMEZONE}},
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Возвращает фабрику сессий поверх общего движка."""

    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный контекстный менеджер сессии.

    При выходе (в т.ч. по исключению) сессия закрывается, а незакрытая
    транзакция откатывается.
    """

    factory = get_session_factory()

    async with factory() as session:
        yield session


async def close_pool() -> None:
    """Освобождает движок и пул соединений (например, при остановке воркера)."""

    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None

    _session_factory = None
