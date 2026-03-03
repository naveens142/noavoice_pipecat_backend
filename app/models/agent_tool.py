from typing import Optional
from sqlalchemy import String, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class AgentTool(BaseModel):
    """Master tool catalog"""
    
    __tablename__ = 'tbl_agent_tools'
    
    tool_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # 'appointment' or 'external'
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_agent_tools_category', 'category'),
        {'schema': 'noavoice_ns'},
    )