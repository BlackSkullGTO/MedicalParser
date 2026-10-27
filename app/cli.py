"""Единая точка входа проекта: `python -m app.cli <команда>`."""

from __future__ import annotations

import argparse
import asyncio
import sys
from alembic import command as alembic_command
from alembic.config import Config

from app.settings import settings
from app.core.sites import SITES_REGISTRY
from app.services.services import UnknownSiteError, run_site, ensure_site_exists
from app.tasks.tasks import download_csv_task
from app.worker import celery_app


def build_parser() -> argparse.ArgumentParser:
    """Собирает парсер аргументов командной строки."""

    parser = argparse.ArgumentParser(
        prog="medical-parser",
        description="Скачивание CSV с медицинских сайтов и сохранение в PostgreSQL.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("sites", help="Показать зарегистрированные сайты.")

    run_task_parser = subparsers.add_parser(
        "run_task",
        help="Запустить задачу без Celery.",
    )
    run_task_parser.add_argument(
        "--site",
        required=True,
        help="Имя сайта из SITES_REGISTRY.",
    )

    add_task_parser = subparsers.add_parser(
        "add_task ",
        help="Поставить задачу в очередь Celery.",
    )
    add_task_parser.add_argument(
        "--site",
        required=True,
        help="Имя сайта из SITES_REGISTRY.",
    )

    worker_parser = subparsers.add_parser("worker", help="Запустить Celery worker.")
    worker_parser.add_argument(
        "--loglevel",
        default="info",
        help="Уровень логирования Celery.",
    )
    worker_parser.add_argument(
        "--concurrency",
        default="1",
        help="Число процессов воркера.",
    )

    migrate_parser = subparsers.add_parser("migrate", help="Применить миграции Alembic.")
    migrate_parser.add_argument("--revision", default="head", help="Целевая ревизия.")

    return parser


def _cmd_sites() -> int:
    if not SITES_REGISTRY:
        print("Реестр сайтов пуст.")
    else:
        print("Зарегистрированные сайты:")

        for name, config in sorted(SITES_REGISTRY.items()):
            auth = "требуется логин" if config.login_required else "без логина"
            print(f"  - {name}: {config.url} ({auth})")

    return 0


def _cmd_run_task(site_name: str) -> int:
    """Запускает задачу без Celery."""

    result = 0

    try:
        task_id = asyncio.run(run_site(site_name))
    except UnknownSiteError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        result = 2
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        result = 1
    else:
        print(f"Готово. Задача {task_id} завершена успешно.")

    return result


def _cmd_add_task(site_name: str) -> int:
    """Ставит задачу в очередь Celery (нужны Redis и запущенный воркер)."""

    result = 0

    try:
        task_id = download_csv_task.delay(site_name)
    except UnknownSiteError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        result = 2
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        result = 1
    else:
        print(f"Задача отправлена в очередь Celery: id={task_id}")

    return result


def _cmd_start_worker(loglevel: str, concurrency: str, extra: list[str]) -> int:
    """Запускает Celery worker через единый CLI (остальные флаги пробрасываются)."""

    argv = [
        "worker",
        f"--loglevel={loglevel}",
        f"--concurrency={concurrency}",
        *extra,
    ]
    celery_app.start(argv=argv)

    return 0


def _cmd_migrate(revision: str) -> int:
    """Применяет миграции Alembic, используя настройки из окружения."""

    alembic_config = Config("alembic.ini")
    
    if settings.ALEMBIC_DATABASE_URL:
        alembic_config.set_main_option("sqlalchemy.url", settings.ALEMBIC_DATABASE_URL)

    alembic_command.upgrade(alembic_config, revision)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)

    # Лишние аргументы допускаются только для worker: они уходят в Celery.
    if extra and args.command != "worker":
        parser.error(f"неизвестные аргументы: {' '.join(extra)}")

    match args.command:
        case "sites":
            result = _cmd_sites()
        case "run_task":
            result = _cmd_run_task(args.site)
        case "add_task":
            result = _cmd_add_task(args.site)
        case "worker":
            result = _cmd_start_worker(args.loglevel, args.concurrency, extra)
        case "migrate":
            result = _cmd_migrate(args.revision)
        case _:
            parser.print_help()
            result = 1

    return result


if __name__ == "__main__":
    sys.exit(main())
