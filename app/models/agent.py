from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import BaseModel


class Agent(BaseModel):
    """Agent model - AI agent configuration"""
    
    __tablename__ = 'tbl_agents'
    
    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('noavoice_ns.tbl_users.id', ondelete='CASCADE'), nullable=False)
    
    # Core Information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Voice & Language
    voice: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default='EN', nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), default='America/Detroit', nullable=False)
    
    # Prompts
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    first_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_call_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voicemail_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration Flags
    first_message_mode: Mapped[str] = mapped_column(String(50), default='assistant-speaks-first', nullable=False)
    end_call_function_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recording_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detect_caller_number: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    multi_lingual_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    agent_actions: Mapped[List['AgentAction']] = relationship('AgentAction', cascade='all, delete-orphan')
    agent_knowledge_bases: Mapped[List['AgentKnowledgeBase']] = relationship('AgentKnowledgeBase', cascade='all, delete-orphan')
    agent_phone: Mapped[Optional['AgentPhone']] = relationship('AgentPhone', cascade='all, delete-orphan', uselist=False)
    
    __table_args__ = (
        Index('idx_agents_user_id', 'user_id'),
        Index('idx_agents_is_deleted', 'is_deleted'),
        {'schema': 'noavoice_ns'},
    )