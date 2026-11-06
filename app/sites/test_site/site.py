"""Конфигурация и адаптер сайта test_site."""

from __future__ import annotations

from app.sites.enums import DownloadEnum, LoginEnum, ParseEnum
from app.sites.base import SiteConfig
from app.sites.registry import register_site
from app.sites.test_site import SITE_KEY


register_site(
    SITE_KEY,
    SiteConfig(
        name='Тестовый сайт',
        url=(
            'https://nsi.rosminzdrav.ru/dictionaries/'
            '1.2.643.5.1.13.13.11.1005/passport/latest'
            '?ysclid=mvfchjewq1253804421'
        ),

        login=LoginEnum.NONE,
        download=DownloadEnum.DROPDOWN,
        parse=ParseEnum.REGULAR,

        download_btn_name='CSV',

        extra={
            'dropdown_btn_name': 'Скачать',
        },
    ),
)
