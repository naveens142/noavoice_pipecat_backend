"""Async Agent Repository"""
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.models.agent import Agent
from app.repository.base_async_repository import BaseAsyncRepository
from app.utils.uuid_helpers import normalize_uuid


class AgentAsyncRepository(BaseAsyncRepository[Agent]):
    """Async agent repository"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, Agent)
    
    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[Agent], int]:
        """Get agents by user ID with pagination"""
        user_uuid = normalize_uuid(user_id)
        if not user_uuid:
            return [], 0
        # Count total
        count_stmt = select(Agent).where(
            and_(
                Agent.user_id == user_uuid,
                Agent.is_deleted == False
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = len(count_result.all())
        
        # Get paginated results
        stmt = select(Agent).where(
            and_(
                Agent.user_id == user_uuid,
                Agent.is_deleted == False  
            )
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total
    
    async def get_by_user_and_id(self, user_id: str, agent_id: str) -> Optional[Agent]:
        """Get agent by user and agent ID (authorization check)"""
        user_uuid = normalize_uuid(user_id)
        agent_uuid = normalize_uuid(agent_id)
        if not user_uuid or not agent_uuid:
            return None
        stmt = select(Agent).where(
            and_(
                Agent.id == agent_uuid,
                Agent.user_id == user_uuid,
                Agent.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_agents(self, user_id: str) -> List[Agent]:
        """Get active agents for user"""
        user_uuid = normalize_uuid(user_id)
        if not user_uuid:
            return []
        stmt = select(Agent).where(
            and_(
                Agent.user_id == user_uuid,
                Agent.is_active == True,
                Agent.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def search_agents(self, user_id: str, search_term: str) -> List[Agent]:
        """Search agents by name or description"""
        user_uuid = normalize_uuid(user_id)
        if not user_uuid:
            return []
        stmt = select(Agent).where(
            and_(
                Agent.user_id == user_uuid,
                Agent.is_deleted == False,
                (Agent.name.ilike(f'%{search_term}%')) | 
                (Agent.description.ilike(f'%{search_term}%'))
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def agent_exists_for_user(self, user_id: str, agent_id: str) -> bool:
        """Check if agent exists and belongs to user"""
        user_uuid = normalize_uuid(user_id)
        agent_uuid = normalize_uuid(agent_id)
        if not user_uuid or not agent_uuid:
            return False
        stmt = select(Agent).where(
            and_(
                Agent.id == agent_uuid,
                Agent.user_id == user_uuid,
                Agent.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
