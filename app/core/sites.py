"""Реестр сайтов и базовый адаптер для скачивания CSV."""

from __future__ import annotations

import csv
import io
from abc import ABC
from dataclasses import dataclass, field
from typing import Optional

from app.core.utils import is_archive, unarchive


@dataclass
class SiteConfig:
    """Конфигурация одного сайта. Добавлять новые сайты — здесь."""

    name: str
    url: str
    download_button_selector: str  # CSS-селектор кнопки «Скачать CSV»
    login_required: bool = False
    login_url: Optional[str] = None
    login_selector_username: Optional[str] = None
    login_selector_password: Optional[str] = None
    login_button_selector: Optional[str] = None
    expected_columns: Optional[list[str]] = None
    # Дополнительные произвольные параметры сайта (селекторы, куки и т.д.)
    extra: dict = field(default_factory=dict)


class BaseSiteAdapter(ABC):
    """Базовый адаптер сайта."""

    def __init__(self, config: SiteConfig):
        self.config = config

    async def login(self, page) -> None:
        """Авторизуется на сайте.
        
        Args:
            page: Ссылка на страницу.
        """

        return None

    async def click_download(self, page) -> None:
        """Нажимает кнопку скачивания CSV.
        
        Args:
            page: Ссылка на страницу.
        """

        await page.get_by_role('button', name='Скачать').click()
        download_button = page.get_by_role('button', name='CSV')
        await download_button.wait_for(state='visible', timeout=10000)
        await download_button.click()

    async def parse_csv(self, content: bytes) -> list[dict]:
        """Парсит байты CSV в список словарей. Можно переопределить.

        Args:
            content: Скачанные данные в байтах.

        Returns:
            Данные после парсинга в формате списка словарей.
        """

        if archive_type := is_archive(content):
            content = unarchive(content, archive_type)
            
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        return [row for row in reader]


# ==================== РЕЕСТР САЙТОВ ====================
# Программист добавляет новые сайты сюда.
# Пример для тестового сайта:
SITES_REGISTRY: dict[str, SiteConfig] = {
    'test_site': SiteConfig(
        name='Международная статистическая классификация болезней и проблем, связанных со здоровьем (10-й пересмотр)',
        url='https://nsi.rosminzdrav.ru/dictionaries/1.2.643.5.1.13.13.11.1005/passport/latest?ysclid=mvfchjewq1253804421',
        download_button_selector='button:text-is("CSV")',
        login_required=False,
    ),
}

# Кастомные адаптеры сайтов.
SITE_ADAPTERS: dict[str, type[BaseSiteAdapter]] = {}
# Пример:
# from app.scraper.adapters.complex_site import ComplexSiteAdapter
# SITE_ADAPTERS["complex_site"] = ComplexSiteAdapter
