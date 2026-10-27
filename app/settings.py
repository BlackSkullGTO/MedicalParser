from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # DSN для asyncpg. Схема строго "postgresql://":
    # asyncpg не понимает суффикс "+asyncpg" (это диалект SQLAlchemy).
    DATABASE_URL: str

    # DSN для Alembic/SQLAlchemy (диалект "postgresql+asyncpg://").
    # Если не задан — Alembic выведет синхронный URL из DATABASE_URL.
    ALEMBIC_DATABASE_URL: Optional[str] = None

    REDIS_URL: str
    DEBUG: bool = False

    PYDEVD_THREAD_DUMP_ON_WARN_EVALUATION_TIMEOUT: bool = False
    PYDEVD_INTERRUPT_THREAD_TIMEOUT: int


settings = Settings()
