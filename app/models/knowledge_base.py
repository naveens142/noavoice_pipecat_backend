from typing import Optional, List
from uuid import UUID
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import BaseModel


class KnowledgeBase(BaseModel):
    """Knowledge base master"""
    
    __tablename__ = 'tbl_knowledge_bases'
    
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, txt, docx, xlsx
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # bytes
    
    uploaded_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('noavoice_ns.tbl_users.id', ondelete='CASCADE'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    agent_knowledge_bases: Mapped[List['AgentKnowledgeBase']] = relationship('AgentKnowledgeBase', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_kb_uploaded_by_user_id', 'uploaded_by_user_id'),
        Index('idx_kb_is_deleted', 'is_deleted'),
        Index('idx_kb_file_type', 'file_type'),
        {'schema': 'noavoice_ns'},
    )