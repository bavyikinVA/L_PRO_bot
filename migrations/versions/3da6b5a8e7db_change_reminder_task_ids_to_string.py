"""change reminder task ids to string

Revision ID: 3da6b5a8e7db
Revises: 95ba4e0437cd
Create Date: 2026-04-30 13:44:59.595861

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3da6b5a8e7db'
down_revision = "95ba4e0437cd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "bookings",
        "reminder_24h_task_id",
        existing_type=sa.Integer(),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using="reminder_24h_task_id::varchar",
    )

    op.alter_column(
        "bookings",
        "reminder_6h_task_id",
        existing_type=sa.Integer(),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using="reminder_6h_task_id::varchar",
    )

    op.alter_column(
        "bookings",
        "reminder_1h_task_id",
        existing_type=sa.Integer(),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using="reminder_1h_task_id::varchar",
    )


def downgrade() -> None:
    op.alter_column(
        "bookings",
        "reminder_24h_task_id",
        existing_type=sa.String(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="NULLIF(reminder_24h_task_id, '')::integer",
    )

    op.alter_column(
        "bookings",
        "reminder_6h_task_id",
        existing_type=sa.String(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="NULLIF(reminder_6h_task_id, '')::integer",
    )

    op.alter_column(
        "bookings",
        "reminder_1h_task_id",
        existing_type=sa.String(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="NULLIF(reminder_1h_task_id, '')::integer",
    )