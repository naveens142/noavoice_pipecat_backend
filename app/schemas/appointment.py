"""
Appointment schemas for booking management.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


class AppointmentBase(BaseModel):
    """Base appointment schema"""
    patient_name: str = Field(..., min_length=1, max_length=255)
    patient_email: EmailStr
    patient_phone: Optional[str] = Field(None, max_length=50)
    patient_timezone: str = Field(default="Asia/Kolkata")
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = Field(default=30, ge=15)
    notes: Optional[str] = None


class CreateAppointmentRequest(AppointmentBase):
    """Create appointment request"""
    agent_id: str = Field(..., description="Agent ID to handle this appointment")
    event_type_id: Optional[int] = None


class UpdateAppointmentRequest(BaseModel):
    """Update appointment request"""
    patient_name: Optional[str] = Field(None, min_length=1, max_length=255)
    patient_email: Optional[EmailStr] = None
    patient_phone: Optional[str] = Field(None, max_length=50)
    patient_timezone: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15)
    notes: Optional[str] = None
    status: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    """Appointment response"""
    id: UUID
    status: str = Field(default="PENDING")
    calcom_booking_id: Optional[int] = None
    calcom_booking_uid: Optional[str] = None
    cancellation_reason: Optional[str] = None
    rescheduling_reason: Optional[str] = None
    livekit_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppointmentDetailResponse(AppointmentResponse):
    """Appointment detail with all information"""
    pass


class PaginatedAppointmentResponse(BaseModel):
    """Paginated appointment response"""
    items: list[AppointmentResponse]
    total: int
    skip: int
    limit: int


class CancelAppointmentRequest(BaseModel):
    """Cancel appointment request"""
    cancellation_reason: str = Field(..., min_length=1, description="Reason for cancellation")


class RescheduleAppointmentRequest(BaseModel):
    """Reschedule appointment request"""
    start_time: datetime = Field(..., description="New appointment start time")
    end_time: Optional[datetime] = None
    rescheduling_reason: Optional[str] = None


class AppointmentStatsResponse(BaseModel):
    """Appointment statistics"""
    total_appointments: int
    pending: int
    accepted: int
    cancelled: int
    rescheduled: int


class AppointmentSearchResponse(BaseModel):
    """Appointment search response"""
    items: list[AppointmentResponse]
    total: int
    page: int
    page_size: int
