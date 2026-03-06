"""
Async appointment service for business logic.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.appointment import AppointmentAsyncRepository
from app.schemas.appointment import (
    CreateAppointmentRequest,
    UpdateAppointmentRequest,
    AppointmentResponse,
    PaginatedAppointmentResponse,
)


class AppointmentAsyncService:
    """Service for appointment operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AppointmentAsyncRepository(db)
    
    async def create_appointment(
        self,
        request: CreateAppointmentRequest,
    ) -> AppointmentResponse:
        """Create a new appointment"""
        appointment = await self.repository.create_appointment(
            patient_name=request.patient_name,
            patient_email=request.patient_email,
            patient_phone=request.patient_phone,
            patient_timezone=request.patient_timezone,
            start_time=request.start_time,
            end_time=request.end_time,
            duration_minutes=request.duration_minutes,
            status="PENDING",
            notes=request.notes,
            event_type_id=request.event_type_id,
        )
        
        await self.db.commit()
        return AppointmentResponse.from_orm(appointment)
    
    async def get_appointment(self, appointment_id: str) -> Optional[AppointmentResponse]:
        """Get appointment by ID"""
        try:
            app_uuid = UUID(appointment_id)
        except ValueError:
            raise ValueError("Invalid appointment ID format")
        
        appointment = await self.repository.get_appointment_by_id(app_uuid)
        if not appointment:
            return None
        
        return AppointmentResponse.from_orm(appointment)
    
    async def list_appointments(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> PaginatedAppointmentResponse:
        """List all appointments"""
        appointments, total = await self.repository.list_appointments(
            skip=skip,
            limit=limit,
            status=status,
        )
        
        return PaginatedAppointmentResponse(
            items=[AppointmentResponse.from_orm(a) for a in appointments],
            total=total,
            skip=skip,
            limit=limit,
        )
    
    async def search_appointments(
        self,
        search_query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> PaginatedAppointmentResponse:
        """Search appointments by name or email"""
        if len(search_query.strip()) < 1:
            raise ValueError("Search query cannot be empty")
        
        appointments, total = await self.repository.search_appointments(
            search_query=search_query,
            skip=skip,
            limit=limit,
        )
        
        return PaginatedAppointmentResponse(
            items=[AppointmentResponse.from_orm(a) for a in appointments],
            total=total,
            skip=skip,
            limit=limit,
        )
    
    async def get_appointments_by_email(
        self,
        email: str,
        skip: int = 0,
        limit: int = 20,
    ) -> PaginatedAppointmentResponse:
        """Get appointments by patient email"""
        appointments, total = await self.repository.get_appointments_by_email(
            email=email,
            skip=skip,
            limit=limit,
        )
        
        return PaginatedAppointmentResponse(
            items=[AppointmentResponse.from_orm(a) for a in appointments],
            total=total,
            skip=skip,
            limit=limit,
        )
    
    async def update_appointment(
        self,
        appointment_id: str,
        request: UpdateAppointmentRequest,
    ) -> Optional[AppointmentResponse]:
        """Update an appointment"""
        try:
            app_uuid = UUID(appointment_id)
        except ValueError:
            raise ValueError("Invalid appointment ID format")
        
        update_data = request.dict(exclude_unset=True)
        appointment = await self.repository.update_appointment(
            app_uuid,
            **update_data,
        )
        
        if not appointment:
            return None
        
        await self.db.commit()
        return AppointmentResponse.from_orm(appointment)
    
    async def cancel_appointment(
        self,
        appointment_id: str,
        reason: str,
    ) -> Optional[AppointmentResponse]:
        """Cancel an appointment"""
        try:
            app_uuid = UUID(appointment_id)
        except ValueError:
            raise ValueError("Invalid appointment ID format")
        
        appointment = await self.repository.cancel_appointment(
            app_uuid,
            reason,
        )
        
        if not appointment:
            return None
        
        await self.db.commit()
        return AppointmentResponse.from_orm(appointment)
    
    async def reschedule_appointment(
        self,
        appointment_id: str,
        new_start_time: datetime,
        new_end_time: Optional[datetime],
        reason: Optional[str] = None,
    ) -> Optional[AppointmentResponse]:
        """Reschedule an appointment"""
        try:
            app_uuid = UUID(appointment_id)
        except ValueError:
            raise ValueError("Invalid appointment ID format")
        
        appointment = await self.repository.reschedule_appointment(
            app_uuid,
            new_start_time,
            new_end_time,
            reason,
        )
        
        if not appointment:
            return None
        
        await self.db.commit()
        return AppointmentResponse.from_orm(appointment)
    
    async def get_appointment_stats(self) -> dict:
        """Get appointment statistics"""
        return await self.repository.get_appointment_stats()
    
    async def delete_appointment(self, appointment_id: str) -> bool:
        """Delete an appointment (admin only)"""
        try:
            app_uuid = UUID(appointment_id)
        except ValueError:
            raise ValueError("Invalid appointment ID format")
        
        deleted = await self.repository.delete_appointment(app_uuid)
        if deleted:
            await self.db.commit()
        
        return deleted
