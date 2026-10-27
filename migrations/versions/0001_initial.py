"""initial tables: download_tasks, parsed_csv_data

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "download_tasks",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("site_name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_download_tasks_site_name", "download_tasks", ["site_name"])
    op.create_index("ix_download_tasks_status", "download_tasks", ["status"])

    op.create_table(
        "parsed_csv_data",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("site_name", sa.String(length=255), nullable=False),
        sa.Column("row_data", postgresql.JSONB(), nullable=False),
        sa.Column("raw_line", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["download_tasks.id"],
            name="fk_parsed_csv_data_task_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_parsed_csv_data_task_id", "parsed_csv_data", ["task_id"])
    op.create_index("ix_parsed_csv_data_site_name", "parsed_csv_data", ["site_name"])


def downgrade() -> None:
    op.drop_index("ix_parsed_csv_data_site_name", table_name="parsed_csv_data")
    op.drop_index("ix_parsed_csv_data_task_id", table_name="parsed_csv_data")
    op.drop_table("parsed_csv_data")

    op.drop_index("ix_download_tasks_status", table_name="download_tasks")
    op.drop_index("ix_download_tasks_site_name", table_name="download_tasks")
    op.drop_table("download_tasks")
