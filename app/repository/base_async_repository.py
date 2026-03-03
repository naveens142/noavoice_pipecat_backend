"""Async base repository for async database operations"""
from typing import TypeVar, Generic, List, Optional, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.models.base import BaseModel
from app.utils.uuid_helpers import normalize_uuid

T = TypeVar('T', bound=BaseModel)


class BaseAsyncRepository(Generic[T]):
    """Generic async base repository with async CRUD operations"""
    
    def __init__(self, db_session: AsyncSession, model: Type[T]):
        self.db = db_session
        self.model = model
    
    async def create(self, obj_in: dict) -> T:
        """Create new record"""
        # Create model instance directly - SQLAlchemy will infer types from model
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get record by ID"""
        id_uuid = normalize_uuid(id)
        if not id_uuid:
            return None
        
        # Build query - only filter by is_deleted if model has that attribute
        where_clause = self.model.id == id_uuid
        if hasattr(self.model, 'is_deleted'):
            where_clause = and_(where_clause, self.model.is_deleted == False)
        
        stmt = select(self.model).where(where_clause)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple[List[T], int]:
        """Get all records with pagination"""
        # Count total
        count_stmt = select(self.model).where(self.model.is_deleted == False)
        count_result = await self.db.execute(count_stmt)
        total = len(count_result.all())
        
        # Get paginated results
        stmt = select(self.model).where(
            self.model.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total
    
    async def update(self, id: str, obj_in: dict) -> Optional[T]:
        """Update record"""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        for key, value in obj_in.items():
            if value is not None and hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        await self.db.flush()
        # Refresh to prevent lazy-loading issues
        await self.db.refresh(db_obj)
        return db_obj
    
    async def soft_delete(self, id: str) -> bool:
        """Soft delete record"""
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        
        # Only soft delete if model has is_deleted attribute
        if not hasattr(db_obj, 'is_deleted'):
            raise AttributeError(f"{self.model.__name__} does not support soft delete")
        
        db_obj.is_deleted = True
        await self.db.flush()
        return True
    
    async def delete_permanent(self, id: str) -> bool:
        """Hard delete record"""
        id_uuid = normalize_uuid(id)
        if not id_uuid:
            return False
        stmt = select(self.model).where(self.model.id == id_uuid)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return False
        
        await self.db.delete(db_obj)
        await self.db.flush()
        return True
    
    async def exists(self, id: str) -> bool:
        """Check if record exists"""
        id_uuid = normalize_uuid(id)
        if not id_uuid:
            return False
        stmt = select(self.model).where(
            and_(
                self.model.id == id_uuid,
                self.model.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
