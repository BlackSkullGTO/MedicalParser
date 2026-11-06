"""Базовые сущности SQLAlchemy: общий Base и переиспользуемые миксины."""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, MetaData, TypeDecorator, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.settings import settings


NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class Base(DeclarativeBase):
    """Общая declarative-база: все модели проекта (и моделей сайтов) наследуют её."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TZDateTime(TypeDecorator):
    """timestamptz, значения которого возвращаются в таймзоне приложения.

    В PostgreSQL момент времени всё равно хранится в UTC, но драйвер
    (asyncpg) отдаёт `timestamptz` как UTC (+00). Чтобы `created_at` /
    `updated_at` отображались в нужной зоне, приводим значение к
    `TIMEZONE` из настроек при записи и при чтении.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        # Наивное время трактуем как время в таймзоне приложения.
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=ZoneInfo(settings.TIMEZONE))

        return value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None

        return value.astimezone(ZoneInfo(settings.TIMEZONE))


class IdMixin:
    """UUID-первичный ключ."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Метки создания и обновления записи."""

    created_at: Mapped[datetime] = mapped_column(
        TZDateTime(),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


__all__ = ['Base', 'IdMixin', 'TimestampMixin', 'TZDateTime']

