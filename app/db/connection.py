from typing import Optional

import asyncpg

from app.settings import settings

_pool: Optional[asyncpg.Pool] = None

POOL_MIN_SIZE = 2
POOL_MAX_SIZE = 10


async def get_pool() -> asyncpg.Pool:
    """Возвращает общий пул соединений к PostgreSQL."""

    global _pool

    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=POOL_MIN_SIZE,
            max_size=POOL_MAX_SIZE,
        )

    return _pool


async def close_pool() -> None:
    """Закрывает пул соединений (например, при остановке приложения)."""

    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
