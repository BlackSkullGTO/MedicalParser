from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import DateTime, String, Uuid, func, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class StatusEnum(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    FAILED = 'failed'
    SUCCESS = 'completed'


class Base(DeclarativeBase):
    pass


class CeleryTask(Base):
    __tablename__ = 'celery_task'

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    site_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    status: Mapped[StatusEnum] = mapped_column(
        SAEnum(
            StatusEnum,
            values_callable=lambda e: [m.value for m in e],
            name='status_enum',
        ),
        default=StatusEnum.PENDING,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
