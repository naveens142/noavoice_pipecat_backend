"""Change hashed_password column type to TEXT

Revision ID: 002
Revises: 001
Create Date: 2026-02-27 12:30:00

This migration changes the hashed_password column from VARCHAR(255) to TEXT
to avoid asyncpg truncation issues with bcrypt hashes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — change hashed_password to TEXT."""
    op.alter_column(
        'tbl_users',
        'hashed_password',
        existing_type=sa.String(255),
        type_=sa.Text(),
        schema='noavoice_ns'
    )


def downgrade() -> None:
    """Downgrade schema — revert to VARCHAR(255)."""
    op.alter_column(
        'tbl_users',
        'hashed_password',
        existing_type=sa.Text(),
        type_=sa.String(255),
        schema='noavoice_ns'
    )
