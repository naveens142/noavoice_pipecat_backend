from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.knowledge_base import KnowledgeBase
from app.repository.base_repository import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    """Knowledge base repository"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, KnowledgeBase)
    
    def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[KnowledgeBase], int]:
        """Get KBs by user ID"""
        query = self.db.query(KnowledgeBase).filter(
            and_(
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.is_deleted == False
            )
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
    
    def get_active_by_user(self, user_id: str) -> List[KnowledgeBase]:
        """Get active KBs for user"""
        return self.db.query(KnowledgeBase).filter(
            and_(
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.is_active == True,
                KnowledgeBase.is_deleted == False
            )
        ).all()
    
    def kb_belongs_to_user(self, kb_id: str, user_id: str) -> bool:
        """Check if KB belongs to user"""
        return self.db.query(KnowledgeBase).filter(
            and_(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.is_deleted == False
            )
        ).first() is not None
    
    def get_by_file_type(self, user_id: str, file_type: str) -> List[KnowledgeBase]:
        """Get KBs by file type"""
        return self.db.query(KnowledgeBase).filter(
            and_(
                KnowledgeBase.uploaded_by_user_id == user_id,
                KnowledgeBase.file_type == file_type,
                KnowledgeBase.is_deleted == False
            )
        ).all()