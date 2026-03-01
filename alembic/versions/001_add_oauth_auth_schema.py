"""Add OAuth authentication schema

Revision ID: 001
Revises: 
Create Date: 2026-02-27 12:20:00

This migration adds:
- tbl_users table with OAuth support (provider, provider_id fields)
- tbl_refresh_tokens table for token rotation and revocation
- AuthProvider enum for LOCAL, GOOGLE, GITHUB auth types
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — add OAuth tables."""
    
    # Create noavoice_ns schema if not exists
    op.execute("CREATE SCHEMA IF NOT EXISTS noavoice_ns")
    
    # Create tbl_users table
    op.create_table(
        'tbl_users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('picture', sa.String(length=500), nullable=True),
        sa.Column('provider', postgresql.ENUM('LOCAL', 'GOOGLE', 'GITHUB', name='authprovider', schema='noavoice_ns'), nullable=False, server_default='LOCAL'),
        sa.Column('provider_id', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='noavoice_ns'
    )
    
    op.create_index(
        op.f('ix_noavoice_ns_tbl_users_email'),
        'tbl_users',
        ['email'],
        unique=True,
        schema='noavoice_ns'
    )
    op.create_index(
        op.f('ix_noavoice_ns_tbl_users_provider_id'),
        'tbl_users',
        ['provider_id'],
        unique=False,
        schema='noavoice_ns'
    )
    
    # Create tbl_refresh_tokens table
    op.create_table(
        'tbl_refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False, unique=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['noavoice_ns.tbl_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='noavoice_ns'
    )
    
    op.create_index(
        'ix_refresh_tokens_token_hash',
        'tbl_refresh_tokens',
        ['token_hash'],
        unique=False,
        schema='noavoice_ns'
    )
    op.create_index(
        'ix_refresh_tokens_user_id',
        'tbl_refresh_tokens',
        ['user_id'],
        unique=False,
        schema='noavoice_ns'
    )


def downgrade() -> None:
    """Downgrade schema — remove OAuth tables."""
    
    # Drop tables
    op.drop_index('ix_refresh_tokens_user_id', table_name='tbl_refresh_tokens', schema='noavoice_ns')
    op.drop_index('ix_refresh_tokens_token_hash', table_name='tbl_refresh_tokens', schema='noavoice_ns')
    op.drop_table('tbl_refresh_tokens', schema='noavoice_ns')
    
    op.drop_index(op.f('ix_noavoice_ns_tbl_users_provider_id'), table_name='tbl_users', schema='noavoice_ns')
    op.drop_index(op.f('ix_noavoice_ns_tbl_users_email'), table_name='tbl_users', schema='noavoice_ns')
    op.drop_table('tbl_users', schema='noavoice_ns')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS noavoice_ns.authprovider")
