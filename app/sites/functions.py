import csv
import io


async def dropdown_download(self, page):
    """Нажимает кнопку скачивания CSV.
    
    Args:
        page: Ссылка на страницу.
    """

    dropdown_btn_name = getattr(self.config, 'dropdown_btn_name', 'Скачать')
    download_btn_name = getattr(self.config, 'download_btn_name', 'CSV')

    await page.get_by_role('button', name=dropdown_btn_name).click()
    download_button = page.get_by_role('button', name=download_btn_name)
    await download_button.wait_for(state='visible', timeout=10000)
    await download_button.click()


async def regular_download(self, page):
    """Нажимает кнопку скачивания CSV.
    
    Args:
        page: Ссылка на страницу.
    """

    download_btn_name = getattr(self.config, 'download_btn_name', 'CSV')

    await page.get_by_role('button', name=download_btn_name).click()


async def none_login(self, page):
    pass


async def regular_parse(self, data: bytes) -> list[dict]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=';')

    return [row for row in reader]
