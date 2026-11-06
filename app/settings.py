"""Единый конфиг проекта.

Все настройки (таймзона, порты и учётные данные PostgreSQL/Redis, флаги
отладки) задаются в одном файле `.env` в корне проекта. Здесь они описаны
один раз и переиспользуются приложением, Alembic и docker-compose.

DSN-строки (`DATABASE_URL`, `ALEMBIC_DATABASE_URL`, `REDIS_URL`) собираются
из этих частей автоматически, поэтому в `.env` достаточно указать
`POSTGRES_*` / `REDIS_*`. При необходимости любой DSN можно переопределить
целиком через `*_DSN`.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    # ===== Общие настройки приложения =====
    DEBUG: bool = False

    # Таймзона приложения. Влияет на Celery и на сессию PostgreSQL:
    # значение функции now()/func.now() (created_at/updated_at)
    # отображается в этой зоне, а не в UTC (+00).
    TIMEZONE: str = 'Europe/Moscow'

    # ===== PostgreSQL =====
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = 'parserdb'
    POSTGRES_USER: str = 'parser'
    POSTGRES_PASSWORD: str = 'parser'

    # ===== Redis =====
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # ===== Контейнер / entrypoint =====
    # Применять ли миграции Alembic при старте контейнера.
    RUN_MIGRATIONS: bool = True

    # ===== Полные DSN (опционально) =====
    # Если заданы — используются как есть и переопределяют сборку из частей.
    DATABASE_DSN: Optional[str] = None
    ALEMBIC_DATABASE_DSN: Optional[str] = None
    REDIS_DSN: Optional[str] = None

    # ===== Отладка Python (debugpy) =====
    PYDEVD_THREAD_DUMP_ON_WARN_EVALUATION_TIMEOUT: bool = False
    PYDEVD_INTERRUPT_THREAD_TIMEOUT: int = 5000

    def _postgres_dsn(self, dialect: str) -> str:
        """Собирает DSN PostgreSQL из частей (с URL-экранированием логина)."""

        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)

        return (
            f'{dialect}://{user}:{password}'
            f'@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    @property
    def DATABASE_URL(self) -> str:
        """DSN для asyncpg. Схема строго 'postgresql://' (без '+asyncpg')."""

        return self.DATABASE_DSN or self._postgres_dsn('postgresql')

    @property
    def ALEMBIC_DATABASE_URL(self) -> str:
        """DSN для Alembic/SQLAlchemy (диалект 'postgresql+asyncpg://')."""

        return self.ALEMBIC_DATABASE_DSN or self._postgres_dsn('postgresql+asyncpg')

    @property
    def REDIS_URL(self) -> str:
        """DSN Redis для Celery (broker/backend)."""

        return self.REDIS_DSN or (
            f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'
        )


settings = Settings()

