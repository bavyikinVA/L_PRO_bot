"""add booking reminders table

Revision ID: cf6b235466c6
Revises: 3da6b5a8e7db
Create Date: 2026-05-05 12:34:47.004162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf6b235466c6'
down_revision: Union[str, None] = '3da6b5a8e7db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table(
        "booking_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hours_before", sa.Integer(), nullable=False),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("booking_id", "hours_before", name="uq_booking_reminder_once"),
    )

    op.create_index("ix_booking_reminders_booking_id", "booking_reminders", ["booking_id"])
    op.create_index("ix_booking_reminders_remind_at", "booking_reminders", ["remind_at"])
    op.create_index("ix_booking_reminders_status", "booking_reminders", ["status"])
    op.create_index("ix_booking_reminders_task_id", "booking_reminders", ["task_id"])
    op.create_index(
        "ix_booking_reminders_status_remind_at",
        "booking_reminders",
        ["status", "remind_at"]
    )


def downgrade():
    op.drop_table("booking_reminders")