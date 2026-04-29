"""Initial revision

Revision ID: a0c85785eab7
Revises: 
Create Date: 2025-09-22 14:47:10.590492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0c85785eab7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # добавляем колонку как nullable
    op.add_column('bookings',
                  sa.Column('is_cancelled', sa.Boolean(), nullable=True)
                  )

    # обновляем все существующие записи значением по умолчанию (False)
    op.execute("UPDATE bookings SET is_cancelled = false WHERE is_cancelled IS NULL")

    # добавляем остальные колонки
    op.add_column('bookings', sa.Column('reminder_24h_task_id', sa.Integer(), nullable=True))
    op.add_column('bookings', sa.Column('reminder_6h_task_id', sa.Integer(), nullable=True))
    op.add_column('bookings', sa.Column('reminder_1h_task_id', sa.Integer(), nullable=True))

    # делаем is_cancelled NOT NULL
    op.alter_column('bookings', 'is_cancelled', nullable=False)

    # создаем индексы
    op.create_index('ix_bookings_cancelled', 'bookings', ['is_cancelled'], unique=False)
    op.create_index('ix_bookings_is_cancelled', 'bookings', ['is_cancelled'], unique=False)


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index('ix_bookings_is_cancelled', table_name='bookings')
    op.drop_index('ix_bookings_cancelled', table_name='bookings')

    # Делаем колонку nullable
    op.alter_column('bookings', 'is_cancelled', nullable=True)

    # Удаляем колонки
    op.drop_column('bookings', 'reminder_1h_task_id')
    op.drop_column('bookings', 'reminder_6h_task_id')
    op.drop_column('bookings', 'reminder_24h_task_id')
    op.drop_column('bookings', 'is_cancelled')
