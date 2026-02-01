"""user task history table

Revision ID: 3227ac46f5ef
Revises: 001
Create Date: 2026-02-01 18:31:39.063551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3227ac46f5ef'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_task_history',
        sa.Column('user_name', sa.String(length=255), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('cost', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_name'], ['users.name'], ),
        sa.PrimaryKeyConstraint('user_name', 'task_id')
    )


def downgrade() -> None:
    op.drop_table('user_task_history')
