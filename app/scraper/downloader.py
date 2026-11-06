"""Универсальный загрузчик CSV через Playwright.

Модуль отвечает только за скачивание и парсинг: он не знает
ни о статусах задач, ни о записи в базу. Оркестрация — в `app.services.download`.
"""

from __future__ import annotations

from playwright.async_api import async_playwright

from app.sites import get_adapter

PAGE_LOAD_TIMEOUT_MS = 30_000
DOWNLOAD_TIMEOUT_MS = 60_000


async def download_site_csv(site_name: str) -> list[dict]:
    """
    Открывает сайт, (опционально) логинится, нажимает кнопку скачивания,
    скачивает CSV и возвращает распарсенные строки.
    """

    adapter = get_adapter(site_name)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            await adapter.goto_page(page, PAGE_LOAD_TIMEOUT_MS)
            await adapter.login(page)
            
            download_info = await adapter.click_download(page, DOWNLOAD_TIMEOUT_MS)
            download = await download_info.value
            path = await download.path()

            if path is None:
                raise RuntimeError("Playwright не вернул путь к скачанному файлу")

            data = path.read_bytes()

            rows = await adapter.parse_csv(data)

            return rows
        finally:
            await browser.close()
