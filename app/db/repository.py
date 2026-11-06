"""Работа с PostgreSQL через SQLAlchemy ORM: задачи и строки сайтов."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import update

from app.db.connection import get_session
from app.db.models import DownloadTask, TaskStatus
from app.sites import SITE_MODELS


class SiteModelsNotRegisteredError(RuntimeError):
    """У сайта не зарегистрированы ORM-модели в SITE_MODELS."""

    def __init__(self, site_name: str) -> None:
        super().__init__(
            f"Для сайта '{site_name}' не зарегистрированы модели "
            f"(sites/{site_name}/models.py → register_site_models)."
        )
        self.site_name = site_name


async def create_task(site_name: str) -> uuid.UUID:
    """Создаёт задачу со статусом 'pending'. Возвращает id."""

    async with get_session() as session:
        task = DownloadTask(
            site_name=site_name,
            status=TaskStatus.PENDING,
        )
        session.add(task)
        await session.commit()

        return task.id


async def update_task_status(
    task_id: uuid.UUID,
    status: TaskStatus,
    last_error: Optional[str] = None,
) -> None:
    """Обновляет статус задачи, текст ошибки и время обновления."""

    async with get_session() as session:
        await session.execute(
            update(DownloadTask)
            .where(DownloadTask.id == task_id)
            .values(status=status, last_error=last_error)
        )
        await session.commit()


async def save_site_rows(
    task_id: uuid.UUID,
    site_name: str,
    rows: list[dict],
) -> None:
    """Сохраняет строки CSV в таблицы сайта через его mapper из SITE_MODELS."""

    if not rows:
        return

    site = SITE_MODELS.get(site_name)

    if site is None:
        raise SiteModelsNotRegisteredError(site_name)

    objects = site['mapper'](rows)

    if not objects:
        return

    async with get_session() as session:
        await site['saver'](session, objects)
        await session.commit()
