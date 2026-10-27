"""Универсальный загрузчик CSV через Playwright.

Модуль отвечает только за скачивание и парсинг: он не знает
ни о статусах задач, ни о записи в базу. Оркестрация — в `app.services.download`.
"""

from __future__ import annotations

import logging

from playwright.async_api import async_playwright

from app.core.sites import (
    SITE_ADAPTERS,
    SITES_REGISTRY,
    BaseSiteAdapter,
    SiteConfig,
)

logger = logging.getLogger(__name__)

PAGE_LOAD_TIMEOUT_MS = 30_000
DOWNLOAD_TIMEOUT_MS = 60_000


def _get_adapter(site_name: str, config: SiteConfig) -> BaseSiteAdapter:
    """Возвращает адаптер сайта.
    
    Args:
        site_name: Название сайта.
        config (SiteConfig): Конфиг сайта.

    Returns:
        Найденный адаптер сайта, либо BaseSiteAdapter.
    """

    adapter_cls = SITE_ADAPTERS.get(site_name, BaseSiteAdapter)

    return adapter_cls(config)


# Возможно придется внести так же в адаптер.
async def download_site_csv(site_name: str) -> list[dict]:
    """
    Открывает сайт, (опционально) логинится, нажимает кнопку скачивания,
    скачивает CSV и возвращает распарсенные строки.
    """

    config: SiteConfig = SITES_REGISTRY[site_name]
    adapter = _get_adapter(site_name, config)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            logger.info("site=%s opening url=%s", site_name, config.url)
            await page.goto(
                config.url,
                wait_until="networkidle",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )

            if config.login_required:
                logger.info("site=%s logging in", site_name)
                await adapter.login(page)

            logger.info("site=%s clicking download button", site_name)
            async with page.expect_download(timeout=DOWNLOAD_TIMEOUT_MS) as download_info:
                await adapter.click_download(page)

            download = await download_info.value
            path = await download.path()

            if path is None:
                raise RuntimeError("Playwright не вернул путь к скачанному файлу")

            content = path.read_bytes()
            logger.info("site=%s downloaded %d bytes", site_name, len(content))

            rows = await adapter.parse_csv(content)
            logger.info("site=%s parsed %d rows", site_name, len(rows))

            return rows
        finally:
            await browser.close()
