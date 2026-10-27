from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _to_sync_url(url: str) -> str:
    """Alembic работает синхронно: приводим DSN к драйверу psycopg2."""

    for prefix in ('postgresql+asyncpg://', 'postgresql://', 'postgres://'):
        if url.startswith(prefix):
            url = "postgresql+psycopg2://" + url[len(prefix):]

    return url


# Приоритет URL: ALEMBIC_DATABASE_URL -> DATABASE_URL -> alembic.ini
db_url = (
    os.getenv("ALEMBIC_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
    or ""
)
config.set_main_option("sqlalchemy.url", _to_sync_url(db_url))

target_metadata = None


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
