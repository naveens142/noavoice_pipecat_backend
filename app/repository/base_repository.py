"""
Base repository class for synchronous database operations.
NOTE: This is a placeholder for legacy sync repositories (knowledge_base, agent_knowledge_base).
All new repositories should use BaseAsyncRepository for async/await support.
"""
from typing import TypeVar, Generic, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository for synchronous ORM operations.
    DEPRECATED: Use BaseAsyncRepository for new code.
    """

    def __init__(self, db_session: Session, model):
        self.db = db_session
        self.model = model

    def create(self, obj_in: dict) -> T:
        """Create new record"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.flush()
        return db_obj

    def get_by_id(self, id: str) -> Optional[T]:
        """Get record by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except:
            return None

    def get_all(self, skip: int = 0, limit: int = 20) -> Tuple[List[T], int]:
        """Get all records with pagination"""
        query = self.db.query(self.model)
        total = query.count()
        records = query.offset(skip).limit(limit).all()
        return records, total

    def update(self, id: str, obj_in: dict) -> Optional[T]:
        """Update record"""
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        self.db.flush()
        return db_obj

    def soft_delete(self, id: str) -> bool:
        """Soft delete record"""
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False
        if hasattr(db_obj, 'is_deleted'):
            db_obj.is_deleted = True
            self.db.flush()
            return True
        return False

    def delete_permanent(self, id: str) -> bool:
        """Hard delete record"""
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.flush()
        return True

    def exists(self, id: str) -> bool:
        """Check if record exists"""
        return self.get_by_id(id) is not None
