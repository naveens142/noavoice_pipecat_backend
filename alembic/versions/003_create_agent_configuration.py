"""Create agent configuration tables

Revision ID: 003
Revises: 8c8a30de2936
Create Date: 2025-03-02

This migration creates the core agent configuration system:
- tbl_agents: Main agent entity
- tbl_agent_tools: Master tool catalog (pre-populated)
- tbl_agent_actions: Agent-tool mapping
- tbl_knowledge_bases: Knowledge base documents
- tbl_agent_knowledge_bases: Agent-KB mapping
- tbl_agent_phones: Agent phone/Twilio config
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '8c8a30de2936'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Create agent configuration tables"""
    
    # Enable UUID extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # ==================== TABLE 1: tbl_agents ====================
    op.create_table(
        'tbl_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('voice', sa.String(255), nullable=True),
        sa.Column('language', sa.String(10), server_default='EN', nullable=False),
        sa.Column('timezone', sa.String(100), server_default='America/Detroit', nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('first_message', sa.Text(), nullable=True),
        sa.Column('end_call_message', sa.Text(), nullable=True),
        sa.Column('voicemail_message', sa.Text(), nullable=True),
        sa.Column('first_message_mode', sa.String(50), server_default='assistant-speaks-first', nullable=False),
        sa.Column('end_call_function_enabled', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('recording_enabled', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('detect_caller_number', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('multi_lingual_enabled', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['noavoice_ns.tbl_users.id'], name='fk_agents_user_id', ondelete='CASCADE'),
        schema='noavoice_ns'
    )
    
    op.create_index('idx_agents_user_id', 'tbl_agents', ['user_id'], schema='noavoice_ns')
    op.create_index('idx_agents_is_deleted', 'tbl_agents', ['is_deleted'], schema='noavoice_ns')
    op.create_index('idx_agents_created_at', 'tbl_agents', ['created_at'], schema='noavoice_ns')
    
    
    # ==================== TABLE 2: tbl_agent_tools ====================
    op.create_table(
        'tbl_agent_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('tool_key', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tool_key', name='uq_agent_tools_tool_key'),
        schema='noavoice_ns'
    )
    
    op.create_index('idx_agent_tools_category', 'tbl_agent_tools', ['category'], schema='noavoice_ns')
    
    # Pre-populate standard tools
    op.execute("""
        INSERT INTO noavoice_ns.tbl_agent_tools (tool_key, display_name, category, description)
        VALUES 
            ('get_available_slots', 'Check Availability Action', 'appointment', 'Check available appointment slots'),
            ('book_appointment', 'Booking Action', 'appointment', 'Book a new appointment'),
            ('get_booking', 'Get Booking Details', 'appointment', 'Retrieve booking details'),
            ('reschedule_appointment', 'Reschedule Action', 'appointment', 'Reschedule an existing appointment'),
            ('cancel_appointment', 'Cancel Action', 'appointment', 'Cancel an appointment'),
            ('get_weather', 'Weather Information', 'external', 'Get weather information');
    """)
    
    
    # ==================== TABLE 3: tbl_agent_actions ====================
    op.create_table(
        'tbl_agent_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('custom_name', sa.String(255), nullable=True),
        sa.Column('start_message', sa.Text(), nullable=True),
        sa.Column('complete_message', sa.Text(), nullable=True),
        sa.Column('failed_message', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['noavoice_ns.tbl_agents.id'], name='fk_agent_actions_agent_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['noavoice_ns.tbl_agent_tools.id'], name='fk_agent_actions_tool_id', ondelete='RESTRICT'),
        sa.UniqueConstraint('agent_id', 'tool_id', name='uq_agent_actions_agent_tool'),
        schema='noavoice_ns'
    )
    
    op.create_index('idx_agent_actions_agent_id', 'tbl_agent_actions', ['agent_id'], schema='noavoice_ns')
    op.create_index('idx_agent_actions_tool_id', 'tbl_agent_actions', ['tool_id'], schema='noavoice_ns')
    
    
    # ==================== TABLE 4: tbl_knowledge_bases ====================
    op.create_table(
        'tbl_knowledge_bases',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(10), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['noavoice_ns.tbl_users.id'], name='fk_kb_uploaded_by_user_id', ondelete='CASCADE'),
        schema='noavoice_ns'
    )
    
    op.create_index('idx_kb_uploaded_by_user_id', 'tbl_knowledge_bases', ['uploaded_by_user_id'], schema='noavoice_ns')
    op.create_index('idx_kb_is_deleted', 'tbl_knowledge_bases', ['is_deleted'], schema='noavoice_ns')
    op.create_index('idx_kb_file_type', 'tbl_knowledge_bases', ['file_type'], schema='noavoice_ns')
    
    
    # ==================== TABLE 5: tbl_agent_knowledge_bases ====================
    op.create_table(
        'tbl_agent_knowledge_bases',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['noavoice_ns.tbl_agents.id'], name='fk_agent_kb_agent_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['noavoice_ns.tbl_knowledge_bases.id'], name='fk_agent_kb_kb_id', ondelete='CASCADE'),
        sa.UniqueConstraint('agent_id', 'knowledge_base_id', name='uq_agent_kb_agent_kb'),
        schema='noavoice_ns'
    )
    
    op.create_index('idx_agent_kb_agent_id', 'tbl_agent_knowledge_bases', ['agent_id'], schema='noavoice_ns')
    op.create_index('idx_agent_kb_kb_id', 'tbl_agent_knowledge_bases', ['knowledge_base_id'], schema='noavoice_ns')
    
    
    # ==================== TABLE 6: tbl_agent_phones ====================
    op.create_table(
        'tbl_agent_phones',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('twilio_account_sid', sa.String(255), nullable=True),
        sa.Column('twilio_auth_token', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['noavoice_ns.tbl_agents.id'], name='fk_agent_phones_agent_id', ondelete='CASCADE'),
        sa.UniqueConstraint('agent_id', name='uq_agent_phones_agent_id'),
        schema='noavoice_ns'
    )
    
    op.create_index('idx_agent_phones_agent_id', 'tbl_agent_phones', ['agent_id'], schema='noavoice_ns')
    op.create_index('idx_agent_phones_is_active', 'tbl_agent_phones', ['is_active'], schema='noavoice_ns')


def downgrade() -> None:
    """Drop all agent configuration tables"""
    
    op.drop_table('tbl_agent_phones', schema='noavoice_ns')
    op.drop_table('tbl_agent_knowledge_bases', schema='noavoice_ns')
    op.drop_table('tbl_knowledge_bases', schema='noavoice_ns')
    op.drop_table('tbl_agent_actions', schema='noavoice_ns')
    op.drop_table('tbl_agent_tools', schema='noavoice_ns')
    op.drop_table('tbl_agents', schema='noavoice_ns')