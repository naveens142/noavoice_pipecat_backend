"""Async Knowledge Base Repository"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.models.knowledge_base import KnowledgeBase
from app.repository.base_async_repository import BaseAsyncRepository


class KnowledgeBaseAsyncRepository(BaseAsyncRepository[KnowledgeBase]):
    """Knowledge base async repository"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, KnowledgeBase)
    
    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[KnowledgeBase], int]:
        """Get KBs by user ID with pagination"""
        # Get total count
        count_stmt = select(KnowledgeBase).where(
            and_(
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.is_deleted == False
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = len(count_result.all())
        
        # Get paginated results
        stmt = select(KnowledgeBase).where(
            and_(
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.is_deleted == False
            )
        ).offset(skip).limit(limit).order_by(KnowledgeBase.created_at.desc())
        
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total
    
    async def get_active_by_user(self, user_id: str) -> List[KnowledgeBase]:
        """Get active KBs for user"""
        stmt = select(KnowledgeBase).where(
            and_(
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.is_active == True,
                KnowledgeBase.is_deleted == False
            )
        ).order_by(KnowledgeBase.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def kb_belongs_to_user(self, kb_id: str, user_id: str) -> bool:
        """Check if KB belongs to user"""
        stmt = select(KnowledgeBase).where(
            and_(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def get_by_file_type(self, user_id: str, file_type: str) -> List[KnowledgeBase]:
        """Get KBs by file type"""
        stmt = select(KnowledgeBase).where(
            and_(
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.file_type == file_type,
                KnowledgeBase.is_deleted == False
            )
        ).order_by(KnowledgeBase.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
