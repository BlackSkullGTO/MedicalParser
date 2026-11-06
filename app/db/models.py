"""Общие ORM-модели проекта (не относящиеся к конкретному сайту)."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class TaskStatus(str, Enum):
    """Статусы задачи скачивания."""

    PENDING = 'pending'
    RUNNING = 'running'
    FAILED = 'failed'
    SUCCESS = 'completed'


class DownloadTask(Base, IdMixin, TimestampMixin):
    """Задача скачивания CSV с сайта (общая для всех сайтов)."""

    __tablename__ = 'download_tasks'

    site_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(
            TaskStatus,
            values_callable=lambda e: [m.value for m in e],
            name='status_enum',
        ),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


__all__ = ['Base', 'IdMixin', 'TimestampMixin', 'TaskStatus', 'DownloadTask']
