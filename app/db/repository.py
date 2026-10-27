"""Работа с PostgreSQL: задачи и строки CSV."""

from __future__ import annotations

import json
import uuid
from typing import Optional

from app.db.connection import get_pool


async def create_task(site_name: str) -> uuid.UUID:
    """Создаёт запись задачи со статусом 'pending'. Возвращает id."""

    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO download_tasks (site_name, status)
            VALUES ($1, 'pending')
            RETURNING id
            """,
            site_name,
        )

        return row["id"]


async def update_task_status(
    task_id: uuid.UUID,
    status: str,
    last_error: Optional[str] = None,
) -> None:
    """Обновляет статус задачи и время обновления."""

    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE download_tasks
            SET status = $2,
                last_error = $3,
                updated_at = now()
            WHERE id = $1
            """,
            task_id,
            status,
            last_error,
        )


async def save_parsed_rows(task_id: uuid.UUID, site_name: str, rows: list[dict]) -> None:
    """Сохраняет распарсенные строки CSV пакетно."""

    if not rows:
        return

    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            for row in rows:
                await conn.execute(
                    """
                    INSERT INTO parsed_csv_data (task_id, site_name, row_data, raw_line)
                    VALUES ($1, $2, $3::jsonb, $4)
                    """,
                    task_id,
                    site_name,
                    json.dumps(row, ensure_ascii=False),
                    None,
                )
