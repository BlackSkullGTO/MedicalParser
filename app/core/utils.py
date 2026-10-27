import bz2
import gzip
import io
import lzma
import zipfile

_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"PK\x03\x04", "zip"),        # обычный ZIP
    (b"PK\x05\x06", "zip"),        # пустой ZIP
    (b"PK\x07\x08", "zip"),        # spanned ZIP
    (b"\x1f\x8b",   "gzip"),
    (b"BZh",        "bzip2"),
    (b"\xfd7zXZ",   "xz"),
    (b"Rar!\x1a\x07", "rar"),
    (b"7z\xbc\xaf\x27\x1c", "7z"),
)


def is_archive(content: bytes) -> str | None:
    """
    Возвращает тип архива ('zip', 'gzip', 'bzip2', 'xz', 'rar', '7z')
    или None, если content — не архив.
    """
    for signature, archive_type in _SIGNATURES:
        if content.startswith(signature):
            return archive_type
        
    return None


def unarchive(content: bytes, archive_type: str) -> bytes:
    """
    Распаковывает архив и возвращает его содержимое.

    Для zip: если внутри один файл — вернёт его содержимое.
             если несколько — вернёт первый CSV (или первый файл, если CSV нет).
    Для gzip/bzip2/xz: возвращает распакованные байты.
    Для rar/7z: требует сторонних библиотек (rarfile/py7zr) — NotImplementedError.
    """

    result = None

    match archive_type:
        case "zip":
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                names = zf.namelist()
                if not names:
                    raise ValueError("ZIP пуст")
                csv_name = next(
                    (n for n in names if n.lower().endswith(".csv")),
                    names[0],
                )
                result = zf.read(csv_name)

        case "gzip":
            result = gzip.decompress(content)

        case "bzip2":
            result = bz2.decompress(content)

        case "xz":
            result = lzma.decompress(content)

        case "rar":
            raise NotImplementedError("rar: нужен пакет rarfile + unrar")

        case "7z":
            raise NotImplementedError("7z: нужен пакет py7zr")

        case _:
            raise ValueError(f"неизвестный тип архива: {archive_type!r}")

    return result