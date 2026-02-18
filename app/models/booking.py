from sqlalchemy import Column, String, DateTime, Integer, Text, Enum
import enum
from app.models.base import BaseModel

class BookingStatus(str, enum.Enum):
    PENDING    = "pending"
    ACCEPTED   = "accepted"
    CANCELLED  = "cancelled"
    RESCHEDULED = "rescheduled"

class Booking(BaseModel):
    __tablename__ = "bookings"
    
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
    
    # Status
    status             = Column(
        Enum(BookingStatus),
        default=BookingStatus.PENDING,
        nullable=False
    )
    
    # Additional info
    cancellation_reason   = Column(Text, nullable=True)
    rescheduling_reason   = Column(Text, nullable=True)
    notes                 = Column(Text, nullable=True)
    
    # Session tracking
    livekit_session_id = Column(String(255), nullable=True)