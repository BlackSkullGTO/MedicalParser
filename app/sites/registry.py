"""Реестры сайтов: конфиги, адаптеры и ORM-модели."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from app.sites.base import BaseSiteAdapter, SiteConfig


SiteMapper = Callable[..., list[Any]]
SiteSaver = Callable[..., Awaitable[None]]


async def default_saver(session: Any, objects: list[Any]) -> None:
    """Запись по умолчанию: обычная вставка объектов в сессию (пер-задачные сайты)."""

    session.add_all(objects)


SITES_REGISTRY: dict[str, SiteConfig] = {}
SITE_ADAPTERS: dict[str, type[BaseSiteAdapter]] = {}
SITE_MODELS: dict[str, dict[str, Any]] = {}


def register_site(
    site_name: str,
    config: SiteConfig,
    adapter: Optional[type[BaseSiteAdapter]] = None,
) -> None:
    """Регистрирует конфиг (и, опционально, адаптер) сайта."""

    SITES_REGISTRY[site_name] = config

    if adapter is not None:
        SITE_ADAPTERS[site_name] = adapter


def register_site_models(
    site_name: str,
    models: list[type],
    mapper: SiteMapper,
    saver: Optional[SiteSaver] = None,
) -> None:
    """Регистрирует ORM-модели сайта, маппер CSV→объекты и способ записи.

    Если `saver` не задан, используется обычная вставка (подходит для сайтов,
    чьи строки хранятся по задачам). Канонические (одна таблица на всех) сайты
    задают свой `saver` — например, полную перезапись справочника.
    """

    SITE_MODELS[site_name] = {
        'models': list(models),
        'mapper': mapper,
        'saver': saver or default_saver,
    }


def get_adapter(site_name: str) -> BaseSiteAdapter:
    """Возвращает адаптер сайта (кастомный или базовый).

    Args:
        site_name: Имя сайта.

    Returns:
        Найденный адаптер сайта, либо BaseSiteAdapter.
    """

    adapter_cls = SITE_ADAPTERS.get(site_name, BaseSiteAdapter)
    config = SITES_REGISTRY[site_name]

    return adapter_cls(site_name, config)


__all__ = [
    'SITES_REGISTRY',
    'SITE_ADAPTERS',
    'SITE_MODELS',
    'register_site',
    'register_site_models',
    'get_adapter',
    'default_saver',
]
