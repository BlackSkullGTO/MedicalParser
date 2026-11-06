"""Сервисный слой: общая логика скачивания CSV.

Используется всеми точками входа: CLI (`app/cli.py`) и Celery-задачей
(`app.tasks.download_csv`). Здесь же — единое место управления статусами.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.sites import SITES_REGISTRY
from app.db.models import TaskStatus
from app.db.repository import create_task, save_site_rows, update_task_status
from app.scraper.downloader import download_site_csv


class UnknownSiteError(ValueError):
    """Сайт не найден в реестре SITES_REGISTRY."""

    def __init__(self, site_name: str) -> None:
        available = ", ".join(sorted(SITES_REGISTRY)) or "<реестр пуст>"
        super().__init__(
            f"Сайт '{site_name}' не найден в реестре. Доступные сайты: {available}"
        )
        self.site_name = site_name


def ensure_site_exists(site_name: str) -> None:
    """Проверяет, что сайт зарегистрирован в SITES_REGISTRY."""

    if site_name not in SITES_REGISTRY:
        raise UnknownSiteError(site_name)


async def run_site(site_name: str, task_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    """
    Полный цикл: создать запись задачи -> скачать CSV -> сохранить строки
    в PostgreSQL -> обновить статус.

    Если `task_id` передан, новая запись не создаётся. Это используется при
    повторных попытках Celery, чтобы не плодить записи в `download_tasks`.
    """

    if task_id is None:
        task_id = await create_task(site_name)

    await update_task_status(task_id, TaskStatus.RUNNING)

    try:
        ensure_site_exists(site_name)
        rows = await download_site_csv(site_name)
        await save_site_rows(task_id, site_name, rows)
    except Exception as exc:
        await update_task_status(task_id, TaskStatus.FAILED, str(exc))
        raise
    else:
        await update_task_status(task_id, TaskStatus.SUCCESS)

    return task_id
