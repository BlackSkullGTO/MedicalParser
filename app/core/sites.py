from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Optional

from app.core.enums import DownloadEnum, LoginEnum, ParseEnum
from app.core.utils import is_archive, unarchive


@dataclass
class SiteConfig:
    """Конфигурация одного сайта. Добавлять новые сайты — здесь."""

    name: str
    url: str

    login = LoginEnum.NONE
    download = DownloadEnum.REGULAR
    parse = ParseEnum.REGULAR

    download_btn_name: str  = 'CSV'

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

        if archive_type := is_archive(content):
            content = unarchive(content, archive_type)

        fn = ParseEnum.get(self.config.parse)
        rows = await fn(self, data)
        self.log('Получил таблицу из %d строк', len(rows))

        return rows


SITES_REGISTRY: dict[str, SiteConfig] = {
    'test_site': SiteConfig(
        name='Тестовый сайт',
        url='https://nsi.rosminzdrav.ru/dictionaries/1.2.643.5.1.13.13.11.1005/passport/latest?ysclid=mvfchjewq1253804421',

        login=LoginEnum.NONE,
        download=DownloadEnum.DROPDOWN,
        parse=ParseEnum.REGULAR,

        download_btn_name='CSV',

        extra={
            'dropdown_btn_name': 'Скачать',
        },
    ),
}

# Кастомные адаптеры сайтов.
SITE_ADAPTERS: dict[str, type[BaseSiteAdapter]] = {}
# Пример:
# from app.scraper.adapters.complex_site import ComplexSiteAdapter
# SITE_ADAPTERS["complex_site"] = ComplexSiteAdapter


def get_adapter(site_name: str) -> BaseSiteAdapter:
    """Возвращает адаптер сайта.
    
    Args:
        site_name: Название сайта.
        config (SiteConfig): Конфиг сайта.

    Returns:
        Найденный адаптер сайта, либо BaseSiteAdapter.
    """

    adapter_cls = SITE_ADAPTERS.get(site_name, BaseSiteAdapter)
    config = SITES_REGISTRY[site_name]

    return adapter_cls(site_name, config)
