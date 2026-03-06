"""
Appointment endpoints for managing bookings via Cal.com integration.

Endpoints:
  GET    /appointments/available-slots  — get available appointment slots
  POST   /appointments/book             — book a new appointment
  GET    /appointments/booking          — get booking details by email
  POST   /appointments/reschedule       — reschedule an appointment
  POST   /appointments/cancel           — cancel an appointment
"""
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import logging

from app.tools.appointments import (
    get_available_slots,
    book_appointment,
    get_booking,
    reschedule_appointment,
    cancel_appointment,
)
from app.config.logging import app_logger

logger = app_logger

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)


# ═══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class AvailableSlotsRequest(BaseModel):
    """Request for available appointment slots"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    timezone: str = Field(default="Asia/Kolkata", description="Timezone for slot retrieval")


class BookAppointmentRequest(BaseModel):
    """Request to book an appointment"""
    datetime_natural: str = Field(..., description="Natural language datetime (e.g., 'tomorrow at 3pm')")
    name: str = Field(..., description="Patient name")
    email: EmailStr = Field(..., description="Patient email")
    phone: Optional[str] = Field(None, description="Patient phone number")
    timezone: str = Field(default="Asia/Kolkata", description="Patient timezone")
    notes: Optional[str] = Field(None, description="Additional notes")


class GetBookingRequest(BaseModel):
    """Request to get booking details"""
    email: EmailStr = Field(..., description="Patient email address")


class RescheduleAppointmentRequest(BaseModel):
    """Request to reschedule an appointment"""
    email: EmailStr = Field(..., description="Patient email address")
    new_start: str = Field(..., description="New datetime (e.g., 'next Tuesday at 2pm')")
    reason: Optional[str] = Field(None, description="Reason for rescheduling")
    timezone: str = Field(default="Asia/Kolkata", description="Timezone")


class CancelAppointmentRequest(BaseModel):
    """Request to cancel an appointment"""
    email: EmailStr = Field(..., description="Patient email address")
    reason: Optional[str] = Field(None, description="Cancellation reason")


# ═══════════════════════════════════════════════════════════════════
# APPOINTMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/available-slots",
    summary="Get available appointment slots",
    description="Retrieve available appointment slots for a specific date"
)
async def get_available_appointment_slots(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    timezone: str = Query(default="Asia/Kolkata", description="Timezone for slot retrieval")
):
    """
    Get available appointment slots for a specific date.
    
    **Parameters:**
    - **date** (required): Date in YYYY-MM-DD format (e.g., 2026-03-15)
    - **timezone** (optional): Timezone (default: Asia/Kolkata)
    
    **Returns:**
    - Available slots with formatted times
    - Message if no slots available
    
    **Example:**
    ```
    GET /appointments/available-slots?date=2026-03-10&timezone=Asia/Kolkata
    ```
    """
    try:
        logger.info(f"📅 Fetching available slots for date: {date}, timezone: {timezone}")
        result = await get_available_slots(date=date, timezone=timezone)
        logger.info(f"✅ Available slots retrieved successfully for {date}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"❌ Error fetching available slots for {date}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available slots: {str(e)}"
        )


@router.post(
    "/book",
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment",
    description="Create a new appointment booking"
)
async def book_new_appointment(request: BookAppointmentRequest):
    """
    Book a new appointment.
    
    **Parameters:**
    - **datetime_natural** (required): Natural language datetime (e.g., "tomorrow at 3pm", "next Tuesday at 2pm")
    - **name** (required): Patient full name
    - **email** (required): Patient email address
    - **phone** (optional): Patient phone number
    - **timezone** (optional): Patient timezone (default: Asia/Kolkata)
    - **notes** (optional): Additional notes or special requests
    
    **Returns:**
    - Success: Booking confirmation with booking ID
    - Failure: Error message with suggested alternative slots
    
    **Example Request:**
    ```json
    {
        "datetime_natural": "tomorrow at 3pm",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "timezone": "America/New_York",
        "notes": "First time patient"
    }
    ```
    """
    try:
        logger.info(f"📅 Booking appointment for {request.name} ({request.email})")
        logger.info(f"   Date/Time: {request.datetime_natural}, Timezone: {request.timezone}")
        
        result = await book_appointment(
            datetime_natural=request.datetime_natural,
            name=request.name,
            email=request.email,
            phone=request.phone,
            timezone=request.timezone,
            notes=request.notes
        )
        logger.info(f"✅ Appointment booked successfully for {request.email}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"❌ Error booking appointment for {request.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to book appointment: {str(e)}"
        )


@router.get(
    "/booking",
    summary="Get booking details",
    description="Retrieve appointment booking details by email address"
)
async def get_appointment_booking(
    email: str = Query(..., description="Patient email address")
):
    """
    Retrieve appointment booking details by email.
    
    **Parameters:**
    - **email** (required): Patient email address
    
    **Returns:**
    - Booking details if found
    - "No booking found" message if no active bookings exist
    
    **Example:**
    ```
    GET /appointments/booking?email=john@example.com
    ```
    """
    try:
        email_lower = email.strip().lower()
        logger.info(f"🔍 Fetching booking details for email: {email_lower}")
        
        result = await get_booking(email=email_lower)
        logger.info(f"✅ Booking details retrieved for {email_lower}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"❌ Error fetching booking for {email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch booking: {str(e)}"
        )


@router.post(
    "/reschedule",
    summary="Reschedule an appointment",
    description="Change the date/time of an existing appointment"
)
async def reschedule_existing_appointment(request: RescheduleAppointmentRequest):
    """
    Reschedule an existing appointment.
    
    **Parameters:**
    - **email** (required): Patient email address
    - **new_start** (required): New datetime in natural language (e.g., "next Friday at 10am")
    - **reason** (optional): Reason for rescheduling
    - **timezone** (optional): Timezone for the new appointment (default: Asia/Kolkata)
    
    **Returns:**
    - Success: Rescheduling confirmation with new date/time
    - Failure: Error message with reason
    
    **Example Request:**
    ```json
    {
        "email": "john@example.com",
        "new_start": "next Friday at 10am",
        "reason": "Conflict with other meeting",
        "timezone": "America/New_York"
    }
    ```
    """
    try:
        email_lower = request.email.strip().lower()
        logger.info(f"🔄 Rescheduling appointment for {email_lower}")
        logger.info(f"   New datetime: {request.new_start}, Reason: {request.reason}")
        
        result = await reschedule_appointment(
            email=email_lower,
            new_start=request.new_start,
            reason=request.reason,
            timezone=request.timezone
        )
        logger.info(f"✅ Appointment rescheduled successfully for {email_lower}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"❌ Error rescheduling appointment for {request.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reschedule appointment: {str(e)}"
        )


@router.post(
    "/cancel",
    summary="Cancel an appointment",
    description="Cancel an existing appointment booking"
)
async def cancel_existing_appointment(request: CancelAppointmentRequest):
    """
    Cancel an existing appointment.
    
    **Parameters:**
    - **email** (required): Patient email address
    - **reason** (optional): Reason for cancellation
    
    **Returns:**
    - Success: Cancellation confirmation with booking ID
    - Failure: Error message with reason
    
    **Example Request:**
    ```json
    {
        "email": "john@example.com",
        "reason": "No longer need the appointment"
    }
    ```
    """
    try:
        email_lower = request.email.strip().lower()
        logger.info(f"❌ Cancelling appointment for {email_lower}")
        logger.info(f"   Reason: {request.reason}")
        
        result = await cancel_appointment(
            email=email_lower,
            reason=request.reason
        )
        logger.info(f"✅ Appointment cancelled successfully for {email_lower}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"❌ Error cancelling appointment for {request.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel appointment: {str(e)}"
        )
