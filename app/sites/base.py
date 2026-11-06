"""Базовые сущности сайтов: конфигурация и адаптер."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Optional

from app.sites.enums import DownloadEnum, LoginEnum, ParseEnum
from app.sites.utils import is_archive, unarchive


@dataclass
class SiteConfig:
    """Конфигурация одного сайта. Добавлять новые сайты — в sites/<site>/site.py."""

    name: str
    url: str

    login: str
    download: str
    parse: str

    download_btn_name: str

    login_url: Optional[str] = None
    login_selector_username: Optional[str] = None
    login_selector_password: Optional[str] = None
    login_button_selector: Optional[str] = None

    columns: Optional[list[str]] = None

    extra: dict = field(default_factory=dict)


class BaseSiteAdapter:
    """Базовый адаптер сайта."""

    def __init__(self, site_name, config: SiteConfig):
        self.site_name = site_name
        self.config = config
        self.logger = logging.getLogger(__name__)

    def log(self, msg: str, *args):
        self.logger.info(f'Сайт {self.site_name}. {msg}', *args)

    async def goto_page(self, page, timeout):
        self.log('Открываю url=%s', self.config.url)

        await page.goto(
            self.config.url,
            wait_until='networkidle',
            timeout=timeout,
        )

    async def login(self, page):
        if not self.config.login == LoginEnum.NONE:
            fn = LoginEnum.get(self.config.login)

            self.log('Авторизовываюсь')

            await fn(self, page)

    async def click_download(self, page, timeout):
        """Нажимает кнопку скачивания CSV.

        Args:
            page: Ссылка на страницу.
            timeout: Таймаут ожидания скачивания, мс.
        """

        fn = DownloadEnum.get(self.config.download)

        self.log('Нажимаю кнопку скачать')
        async with page.expect_download(timeout=timeout) as download_info:
            await fn(self, page)

        return download_info

    async def parse_csv(self, data: bytes) -> list[dict]:
        """Парсит байты CSV в список словарей. Можно переопределить.

        Args:
            data: Скачанные данные в байтах.

        Returns:
            Данные после парсинга в формате списка словарей.
        """

        self.log('Скачал %d байтов', len(data))

        if archive_type := is_archive(data):
            data = unarchive(data, archive_type)

        fn = ParseEnum.get(self.config.parse)
        rows = await fn(self, data)
        self.log('Получил таблицу из %d строк', len(rows))

        return rows


__all__ = ['SiteConfig', 'BaseSiteAdapter']
