from typing import Optional
from uuid import UUID
from sqlalchemy import String, Text, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import BaseModel


class AgentAction(BaseModel):
    """Agent-Tool mapping"""
    
    __tablename__ = 'tbl_agent_actions'
    
    agent_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('noavoice_ns.tbl_agents.id', ondelete='CASCADE'), nullable=False)
    tool_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('noavoice_ns.tbl_agent_tools.id', ondelete='RESTRICT'), nullable=False)
    
    custom_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    complete_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failed_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    tool: Mapped['AgentTool'] = relationship('AgentTool', foreign_keys=[tool_id])
    
    __table_args__ = (
        Index('idx_agent_actions_agent_id', 'agent_id'),
        Index('idx_agent_actions_tool_id', 'tool_id'),
        UniqueConstraint('agent_id', 'tool_id', name='uq_agent_actions_agent_tool'),
        {'schema': 'noavoice_ns'},
    )