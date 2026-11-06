"""Реестры сайтов и авто-загрузка их конфигов и ORM-моделей."""

from __future__ import annotations

import importlib
import pkgutil

from app.sites.base import BaseSiteAdapter, SiteConfig
from app.sites.registry import (
    SITE_ADAPTERS,
    SITE_MODELS,
    SITES_REGISTRY,
    get_adapter,
    register_site,
    register_site_models,
)


def _import_optional(dotted_path: str) -> None:
    """Импортирует модуль, игнорируя только его отсутствие."""

    try:
        importlib.import_module(dotted_path)
    except ModuleNotFoundError as exc:
        if exc.name != dotted_path:
            raise


def _discover_sites() -> None:
    """Подтягивает sites/<site>/site.py и sites/<site>/models.py всех сайтов.

    Импорт моделей нужен, чтобы Alembic «видел» их таблицы в Base.metadata.
    """

    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith('_') or not module.ispkg:
            continue

        _import_optional(f'{__name__}.{module.name}.site')
        _import_optional(f'{__name__}.{module.name}.models')


_discover_sites()


__all__ = [
    'BaseSiteAdapter',
    'SiteConfig',
    'SITES_REGISTRY',
    'SITE_ADAPTERS',
    'SITE_MODELS',
    'get_adapter',
    'register_site',
    'register_site_models',
]
