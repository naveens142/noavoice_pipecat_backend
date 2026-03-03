from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from app.config.settings import settings
import uuid

class Base(DeclarativeBase):
    """Base class for all models with configurable schema support"""
    # Set the schema for all tables
    __table_args__ = {'schema': settings.DB_SCHEMA}

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )