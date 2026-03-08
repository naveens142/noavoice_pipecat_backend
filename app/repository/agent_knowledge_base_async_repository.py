"""Async Agent Knowledge Base Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.models.agent_knowledge_base import AgentKnowledgeBase
from app.repository.base_async_repository import BaseAsyncRepository


class AgentKnowledgeBaseAsyncRepository(BaseAsyncRepository[AgentKnowledgeBase]):
    """Agent Knowledge Base async repository"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, AgentKnowledgeBase)
    
    async def get_by_agent_id(self, agent_id: str) -> List[AgentKnowledgeBase]:
        """Get all KBs for agent"""
        stmt = select(AgentKnowledgeBase).where(
            and_(
                AgentKnowledgeBase.agent_id == agent_id,
                AgentKnowledgeBase.is_deleted == False
            )
        ).order_by(AgentKnowledgeBase.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def kb_assigned_to_agent(self, agent_id: str, kb_id: str) -> bool:
        """Check if KB already assigned to agent"""
        stmt = select(AgentKnowledgeBase).where(
            and_(
                AgentKnowledgeBase.agent_id == agent_id,
                AgentKnowledgeBase.knowledge_base_id == kb_id,
                AgentKnowledgeBase.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def remove_kb_from_agent(self, agent_id: str, kb_id: str) -> bool:
        """Remove KB from agent (soft delete)"""
        stmt = select(AgentKnowledgeBase).where(
            and_(
                AgentKnowledgeBase.agent_id == agent_id,
                AgentKnowledgeBase.knowledge_base_id == kb_id
            )
        )
        result = await self.db.execute(stmt)
        kb_assignment = result.scalar_one_or_none()
        
        if not kb_assignment:
            return False
        
        kb_assignment.is_deleted = True
        await self.db.flush()
        return True
    
    async def get_agent_kbs_with_details(self, agent_id: str):
        """Get all KBs for agent with knowledge base details loaded"""
        from sqlalchemy.orm import selectinload
        
        stmt = select(AgentKnowledgeBase).where(
            and_(
                AgentKnowledgeBase.agent_id == agent_id,
                AgentKnowledgeBase.is_deleted == False
            )
        ).options(
            selectinload(AgentKnowledgeBase.knowledge_base)
        ).order_by(AgentKnowledgeBase.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
