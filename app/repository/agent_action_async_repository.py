"""Async Agent Action Repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.models.agent_action import AgentAction
from app.models.agent_tool import AgentTool
from app.repository.base_async_repository import BaseAsyncRepository
from app.utils.uuid_helpers import normalize_uuid


class AgentActionAsyncRepository(BaseAsyncRepository[AgentAction]):
    """Async agent action repository"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, AgentAction)
    
    async def get_by_agent_id(self, agent_id: str) -> List[AgentAction]:
        """Get all actions for agent"""
        agent_uuid = normalize_uuid(agent_id)
        if not agent_uuid:
            return []
        stmt = select(AgentAction).where(
            and_(
                AgentAction.agent_id == agent_uuid,
                AgentAction.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_agent_and_tool(self, agent_id: str, tool_id: str) -> Optional[AgentAction]:
        """Get specific action"""
        agent_uuid = normalize_uuid(agent_id)
        tool_uuid = normalize_uuid(tool_id)
        if not agent_uuid or not tool_uuid:
            return None
        stmt = select(AgentAction).where(
            and_(
                AgentAction.agent_id == agent_uuid,
                AgentAction.tool_id == tool_uuid,
                AgentAction.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_actions_with_tools(self, agent_id: str) -> List[dict]:
        """Get agent actions with tool details"""
        agent_uuid = normalize_uuid(agent_id)
        if not agent_uuid:
            return []
        stmt = select(
            AgentAction.id,
            AgentAction.agent_id,
            AgentAction.tool_id,
            AgentAction.custom_name,
            AgentAction.start_message,
            AgentAction.complete_message,
            AgentAction.failed_message,
            AgentAction.is_enabled,
            AgentTool.tool_key,
            AgentTool.display_name,
            AgentTool.category
        ).join(AgentTool).where(
            and_(
                AgentAction.agent_id == agent_uuid,
                AgentAction.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        actions = result.all()
        
        return [
            {
                'id': action.id,
                'agent_id': action.agent_id,
                'tool_id': action.tool_id,
                'custom_name': action.custom_name,
                'start_message': action.start_message,
                'complete_message': action.complete_message,
                'failed_message': action.failed_message,
                'is_enabled': action.is_enabled,
                'tool_key': action.tool_key,
                'display_name': action.display_name,
                'category': action.category,
            }
            for action in actions
        ]
    
    async def tool_already_added(self, agent_id: str, tool_id: str) -> bool:
        """Check if tool already added to agent"""
        agent_uuid = normalize_uuid(agent_id)
        tool_uuid = normalize_uuid(tool_id)
        if not agent_uuid or not tool_uuid:
            return False
        stmt = select(AgentAction).where(
            and_(
                AgentAction.agent_id == agent_uuid,
                AgentAction.tool_id == tool_uuid,
                AgentAction.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
