from app.sites.functions import (
    dropdown_download,
    none_login,
    regular_download,
    regular_parse,
)


class BaseEnumerate:
    values = {}

    @classmethod
    def get(cls, key):
        return cls.values.get(key)
    

class DownloadEnum(BaseEnumerate):

    REGULAR = 'regular'
    DROPDOWN = 'dropdown'

    values = {
        REGULAR: regular_download,
        DROPDOWN: dropdown_download,
    }


class LoginEnum(BaseEnumerate):

    NONE = 'none'

    values = {
        NONE: none_login,
    }


class ParseEnum(BaseEnumerate):

    REGULAR = 'regular'

    values = {
        REGULAR: regular_parse,
    }
