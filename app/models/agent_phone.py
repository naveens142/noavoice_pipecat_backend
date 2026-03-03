from typing import Optional
from uuid import UUID
from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class AgentPhone(BaseModel):
    """Agent phone/Twilio config"""
    
    __tablename__ = 'tbl_agent_phones'
    
    agent_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('noavoice_ns.tbl_agents.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    twilio_account_sid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    twilio_auth_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        Index('idx_agent_phones_agent_id', 'agent_id'),
        Index('idx_agent_phones_is_active', 'is_active'),
        {'schema': 'noavoice_ns'},
    )