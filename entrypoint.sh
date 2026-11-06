#!/bin/sh
# Точка входа контейнера: ждём PostgreSQL, применяем миграции и запускаем
# переданную команду (по умолчанию — Celery worker).
set -e

# Ожидание готовности PostgreSQL. Пропускается, если POSTGRES_HOST не задан.
wait_for_db() {
    if [ -z "$POSTGRES_HOST" ]; then
        return 0
    fi

    echo "Ожидание PostgreSQL на ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."

    python - "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}" <<'PY'
import socket
import sys
import time

host, port = sys.argv[1], int(sys.argv[2])
attempts = 60

for attempt in range(1, attempts + 1):
    try:
        with socket.create_connection((host, port), timeout=2):
            print('PostgreSQL доступен.')
            break
    except OSError:
        print(f'  попытка {attempt}/{attempts}...')
        time.sleep(2)
else:
    raise SystemExit('Не удалось дождаться PostgreSQL.')
PY
}

wait_for_db

# Применение миграций (можно отключить: RUN_MIGRATIONS=0).
case "${RUN_MIGRATIONS:-1}" in
    0|false|False|no|No)
        echo 'Миграции пропущены (RUN_MIGRATIONS=0).'
        ;;
    *)
        echo 'Применение миграций Alembic...'
        python -m app.cli migrate
        ;;
esac

exec "$@"
