from sqlalchemy import Column, String, DateTime, Integer, Text, Enum, CheckConstraint
import enum
from app.models.base import BaseModel
from app.config.settings import settings

class BookingStatus(str, enum.Enum):
    PENDING    = "PENDING"
    ACCEPTED   = "ACCEPTED"
    CANCELLED  = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"

class Booking(BaseModel):
    __tablename__ = "tbl_bookings"
    
    # Cal.com identifiers
    calcom_booking_id  = Column(Integer, nullable=True)
    calcom_booking_uid = Column(String(255), nullable=True, index=True)
    
    # Patient info
    patient_name       = Column(String(255), nullable=False)
    patient_email      = Column(String(255), nullable=False, index=True)
    patient_phone      = Column(String(50), nullable=True) 
    patient_timezone   = Column(String(100), default="Asia/Kolkata")
    
    # Appointment info
    start_time         = Column(DateTime(timezone=True), nullable=False)
    end_time           = Column(DateTime(timezone=True), nullable=True)
    event_type_id      = Column(Integer, nullable=False)
    duration_minutes   = Column(Integer, default=30)
    
    # Status - Use VARCHAR instead of native enum to avoid asyncpg cache issues
    status             = Column(
        String(50),
        default="PENDING",
        nullable=False
    )
    
    # Additional info
    cancellation_reason   = Column(Text, nullable=True)
    rescheduling_reason   = Column(Text, nullable=True)
    notes                 = Column(Text, nullable=True)
    
    # Session tracking
    livekit_session_id = Column(String(255), nullable=True)
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            f"status IN ('PENDING', 'ACCEPTED', 'CANCELLED', 'RESCHEDULED')",
            name="check_booking_status"
        ),
    )