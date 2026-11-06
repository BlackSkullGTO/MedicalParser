"""Сборка Celery-приложения."""

from __future__ import annotations

from celery import Celery

from app.settings import settings

celery_app = Celery(
    "medical_parser",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Таймзона берётся из единого конфига (.env: TIMEZONE).
    timezone=settings.TIMEZONE,
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
