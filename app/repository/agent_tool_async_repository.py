"""Async Agent Tool Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.models.agent_tool import AgentTool
from app.repository.base_async_repository import BaseAsyncRepository


class AgentToolAsyncRepository(BaseAsyncRepository[AgentTool]):
    """Async agent tool repository"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, AgentTool)

    async def get_by_tool_key(self, tool_key: str) -> Optional[AgentTool]:
        """Get tool by key"""
        stmt = select(AgentTool).where(AgentTool.tool_key == tool_key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_tools(self) -> List[AgentTool]:
        """Get all active tools"""
        stmt = select(AgentTool).where(AgentTool.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_category(self, category: str) -> List[AgentTool]:
        """Get tools by category"""
        stmt = select(AgentTool).where(
            and_(
                AgentTool.category == category,
                AgentTool.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
