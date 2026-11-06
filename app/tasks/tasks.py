"""Celery-задача на скачивание CSV с сайта."""

from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from celery.utils.time import get_exponential_backoff_interval

from app.db.connection import close_pool
from app.services.services import run_site
from app.worker import celery_app

MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 1
RETRY_BACKOFF_MAX = 600
RETRY_JITTER = True


async def celery_run_task(site_name: str, task_id: Optional[uuid.UUID]) -> uuid.UUID:
    try:
        return await run_site(site_name, task_id)
    finally:
        await close_pool()


@celery_app.task(bind=True, name="app.tasks.download_csv.download_csv_task")
def download_csv_task(self, site_name: str, task_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    """
    Скачивает CSV с указанного сайта и сохраняет строки в PostgreSQL.

    `task_id` создаётся один раз — при первой попытке — и переиспользуется
    при повторных, чтобы не плодить записи в `download_tasks`.
    """

    try:
        task_id = asyncio.run(celery_run_task(site_name, task_id))

        return str(task_id)
    
    except Exception as exc:
        countdown = get_exponential_backoff_interval(
            factor=RETRY_BACKOFF_FACTOR,
            retries=self.request.retries,
            maximum=RETRY_BACKOFF_MAX,
            full_jitter=RETRY_JITTER,
        )
        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=MAX_RETRIES,
            args=(),
            kwargs={'site_name': site_name, 'task_id': task_id},
        )
