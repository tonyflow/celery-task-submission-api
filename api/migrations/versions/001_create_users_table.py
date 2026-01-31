"""Create users table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("api_key", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("credits", sa.Integer, nullable=False),
    )

    op.execute(
        """
        INSERT INTO users (name, api_key, credits) VALUES
        ('admin',      '123e4567-e89b-12d3-a456-426614174000', 1000),
        ('test_user1', '550e8400-e29b-41d4-a716-446655440000',  500),
        ('test_user2', 'c56a4180-65aa-42ec-a945-5fd21dec0538',  250)
        """
    )


def downgrade() -> None:
    op.drop_table("users")
