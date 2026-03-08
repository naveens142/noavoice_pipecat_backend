from uuid import UUID
from sqlalchemy import String, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import BaseModel


class AgentKnowledgeBase(BaseModel):
    """Agent-KB mapping"""
    
    __tablename__ = 'tbl_agent_knowledge_bases'
    
    agent_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('noavoice_ns.tbl_agents.id', ondelete='CASCADE'), nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('noavoice_ns.tbl_knowledge_bases.id', ondelete='CASCADE'), nullable=False)
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    knowledge_base: Mapped['KnowledgeBase'] = relationship('KnowledgeBase', overlaps='agent_knowledge_bases')
    
    __table_args__ = (
        Index('idx_agent_kb_agent_id', 'agent_id'),
        Index('idx_agent_kb_kb_id', 'knowledge_base_id'),
        UniqueConstraint(
            'agent_id',
            'knowledge_base_id',
            name='uq_agent_kb_agent_kb'
        ),
        {'schema': 'noavoice_ns'},
    )