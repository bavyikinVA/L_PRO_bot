"""remove old reminder task fields from bookings

Revision ID: 4424cdf66261
Revises: cf6b235466c6
Create Date: 2026-05-05 13:00:01.895776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4424cdf66261'
down_revision: Union[str, None] = 'cf6b235466c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.drop_column("bookings", "reminder_24h_task_id")
    op.drop_column("bookings", "reminder_6h_task_id")
    op.drop_column("bookings", "reminder_1h_task_id")


def downgrade():
    op.add_column(
        "bookings",
        sa.Column("reminder_24h_task_id", sa.String(), nullable=True)
    )
    op.add_column(
        "bookings",
        sa.Column("reminder_6h_task_id", sa.String(), nullable=True)
    )
    op.add_column(
        "bookings",
        sa.Column("reminder_1h_task_id", sa.String(), nullable=True)
    )
