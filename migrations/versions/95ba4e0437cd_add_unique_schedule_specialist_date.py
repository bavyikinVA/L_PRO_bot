"""add unique schedule specialist date

Revision ID: 95ba4e0437cd
Revises: 12a27b2531e0
Create Date: 2026-04-30 13:29:30.854891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95ba4e0437cd'
down_revision: Union[str, None] = '12a27b2531e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_unique_constraint(
        "uq_schedule_specialist_date",
        "schedules",
        ["specialist_id", "work_date"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_schedule_specialist_date",
        "schedules",
        type_="unique"
    )