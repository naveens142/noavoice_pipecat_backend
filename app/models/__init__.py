"""Import all models to register them with Base.metadata"""
from app.models.base import Base, BaseModel
from app.models.booking import Booking

__all__ = ["Base", "BaseModel", "Booking"]
