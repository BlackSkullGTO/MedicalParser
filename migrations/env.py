from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app.sites  # noqa: F401  # регистрирует ORM-модели всех сайтов в Base.metadata
from app.db.models import Base
from app.settings import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _to_sync_url(url: str) -> str:
    """Alembic работает синхронно: приводим DSN к драйверу psycopg2."""

    for prefix in ('postgresql+asyncpg://', 'postgresql://', 'postgres://'):
        if url.startswith(prefix):
            url = "postgresql+psycopg2://" + url[len(prefix):]

    return url


# Единый источник DSN — app.settings (значения из .env).
db_url = settings.ALEMBIC_DATABASE_URL or config.get_main_option("sqlalchemy.url") or ""
config.set_main_option("sqlalchemy.url", _to_sync_url(db_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Миграция без подключения к базе."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Миграция с подключением к базе."""

    configuration = {
        "sqlalchemy.url": config.get_main_option("sqlalchemy.url"),
    }
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Таймзона сессии PostgreSQL для миграций (created_at/updated_at).
        connect_args={"options": f"-c timezone={settings.TIMEZONE}"},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
