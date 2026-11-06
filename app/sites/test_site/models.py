"""ORM-модели сайта test_site — справочник МКБ.

Данные — дерево: у строки есть внешний идентификатор (`external_id` из CSV)
и ссылка на родителя по этому же внешнему id (`parent_external_id`).
Таблица каноническая: хранится одна копия справочника (без привязки к задаче).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    delete,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.sites.registry import register_site_models
from app.sites.test_site import SITE_KEY


class MkbRecord(Base, IdMixin, TimestampMixin):
    """Строка справочника МКБ. Дерево через parent_external_id → external_id."""

    __tablename__ = 'mkb_records'

    external_id: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
    )
    parent_external_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            'mkb_records.external_id',
            ondelete='SET NULL',
            deferrable=True,
            initially='DEFERRED',
        ),
        nullable=True,
        index=True,
    )
    rec_code: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    addl_code: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    actual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    parent: Mapped[Optional['MkbRecord']] = relationship(
        remote_side='MkbRecord.external_id',
        back_populates='children',
    )
    children: Mapped[list['MkbRecord']] = relationship(back_populates='parent')


def _to_int(value: Optional[str]) -> Optional[int]:
    value = (value or '').strip()

    return int(value) if value else None


def _to_bool(value: Optional[str]) -> bool:
    return (value or '').strip() in ('1', 'true', 'True', 'yes')


def _to_date(value: Optional[str]) -> Optional[datetime.date]:
    value = (value or '').strip()

    if value:
        result = datetime.datetime.strptime(value, '%d.%m.%Y').date()
    else:
        result = None

    return result


def map_rows(rows: list[dict]) -> list[MkbRecord]:
    """Преобразует строки CSV справочника в объекты MkbRecord."""

    return [
        MkbRecord(
            external_id=int(row['ID']),
            parent_external_id=_to_int(row.get('ID_PARENT')),
            rec_code=row['REC_CODE'],
            code=row['MKB_CODE'],
            name=row['MKB_NAME'],
            addl_code=_to_int(row.get('ADDL_CODE')),
            actual=_to_bool(row.get('ACTUAL')),
            date=_to_date(row.get('DATE')),
        )
        for row in rows
    ]


async def replace_all(session: AsyncSession, objects: list[MkbRecord]) -> None:
    """Полная перезамена справочника: очистка таблицы + вставка.

    Отложенный (DEFERRABLE) self-FK позволяет вставлять дерево в любом порядке.
    """

    await session.execute(delete(MkbRecord))
    session.add_all(objects)


register_site_models(
    SITE_KEY,
    models=[MkbRecord],
    mapper=map_rows,
    saver=replace_all,
)
