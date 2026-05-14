"""add phone hash to users

Revision ID: 2f4a2a7905e7
Revises: 4424cdf66261
Create Date: 2026-05-14 13:41:41.803975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f4a2a7905e7'
down_revision: Union[str, None] = '4424cdf66261'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_hash", sa.String(), nullable=True))
    op.create_index("ix_users_phone_hash", "users", ["phone_hash"])


def downgrade() -> None:
    op.drop_index("ix_users_phone_hash", table_name="users")
    op.drop_column("users", "phone_hash")