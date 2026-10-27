from enum import Enum

from app.core.functions import dropdown_download, none_login, regular_download, regular_parse


class GetEnum(str, Enum):
    values = {}

    @classmethod
    def get(cls, key):
        return cls.values.get(key)


class DownloadEnum(GetEnum):

    REGULAR = 'regular'
    DROPDOWN = 'dropdown'

    values = {
        REGULAR: regular_download,
        DROPDOWN: dropdown_download,
    }


class LoginEnum(GetEnum):

    NONE = 'none'

    values = {
        NONE: none_login,
    }


class ParseEnum(GetEnum):

    REGULAR = 'regular'

    values = {
        REGULAR: regular_parse,
    }
