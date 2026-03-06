"""
Async appointment repository for database operations.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.booking import Booking, BookingStatus
from app.repository.base_async_repository import BaseAsyncRepository


class AppointmentAsyncRepository(BaseAsyncRepository):
    """Async repository for appointment operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Booking)
    
    async def create_appointment(
        self,
        patient_name: str,
        patient_email: str,
        patient_phone: Optional[str],
        patient_timezone: str,
        start_time: datetime,
        end_time: Optional[datetime],
        duration_minutes: int,
        status: str = "PENDING",
        notes: Optional[str] = None,
        event_type_id: Optional[int] = None,
    ) -> Booking:
        """Create a new appointment"""
        appointment = Booking(
            patient_name=patient_name,
            patient_email=patient_email,
            patient_phone=patient_phone,
            patient_timezone=patient_timezone,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            status=status,
            notes=notes,
            event_type_id=event_type_id or 0,
        )
        self.db.add(appointment)
        await self.db.flush()
        await self.db.refresh(appointment)
        return appointment
    
    async def get_appointment_by_id(self, appointment_id: UUID) -> Optional[Booking]:
        """Get appointment by ID"""
        query = select(Booking).where(Booking.id == str(appointment_id))
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_appointments_by_email(
        self,
        email: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Booking], int]:
        """Get appointments for a patient email with pagination"""
        # Total count
        count_query = select(Booking.__table__.columns.id).where(
            Booking.patient_email == email
        )
        count_result = await self.db.execute(
            select(Booking).from_statement(count_query)
        )
        
        # Paginated results
        query = select(Booking).where(
            Booking.patient_email == email
        ).order_by(desc(Booking.start_time)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        appointments = result.scalars().all()
        
        # Get total count
        count_query = select(Booking).where(Booking.patient_email == email)
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return appointments, total
    
    async def list_appointments(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[Booking], int]:
        """List all appointments with optional status filter"""
        query_base = select(Booking)
        
        if status:
            query_base = query_base.where(Booking.status == status)
        
        # Get total count
        count_result = await self.db.execute(query_base)
        total = len(count_result.scalars().all())
        
        # Get paginated results
        query = query_base.order_by(
            desc(Booking.start_time)
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        appointments = result.scalars().all()
        
        return appointments, total
    
    async def search_appointments(
        self,
        search_query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Booking], int]:
        """Search appointments by patient name or email"""
        query_base = select(Booking).where(
            or_(
                Booking.patient_name.ilike(f"%{search_query}%"),
                Booking.patient_email.ilike(f"%{search_query}%"),
            )
        )
        
        # Get total count
        count_result = await self.db.execute(query_base)
        total = len(count_result.scalars().all())
        
        # Get paginated results
        query = query_base.order_by(
            desc(Booking.start_time)
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        appointments = result.scalars().all()
        
        return appointments, total
    
    async def update_appointment(
        self,
        appointment_id: UUID,
        **kwargs
    ) -> Optional[Booking]:
        """Update appointment fields"""
        appointment = await self.get_appointment_by_id(appointment_id)
        if not appointment:
            return None
        
        # Update allowed fields
        allowed_fields = {
            'patient_name', 'patient_email', 'patient_phone',
            'patient_timezone', 'start_time', 'end_time',
            'duration_minutes', 'status', 'notes',
            'cancellation_reason', 'rescheduling_reason',
            'livekit_session_id'
        }
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(appointment, key, value)
        
        await self.db.flush()
        await self.db.refresh(appointment)
        return appointment
    
    async def cancel_appointment(
        self,
        appointment_id: UUID,
        reason: str,
    ) -> Optional[Booking]:
        """Cancel an appointment"""
        return await self.update_appointment(
            appointment_id,
            status="CANCELLED",
            cancellation_reason=reason,
        )
    
    async def reschedule_appointment(
        self,
        appointment_id: UUID,
        new_start_time: datetime,
        new_end_time: Optional[datetime],
        reason: Optional[str] = None,
    ) -> Optional[Booking]:
        """Reschedule an appointment"""
        return await self.update_appointment(
            appointment_id,
            status="RESCHEDULED",
            start_time=new_start_time,
            end_time=new_end_time,
            rescheduling_reason=reason,
        )
    
    async def get_appointments_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Booking], int]:
        """Get appointments filtered by status"""
        query_base = select(Booking).where(Booking.status == status)
        
        # Get total count
        count_result = await self.db.execute(query_base)
        total = len(count_result.scalars().all())
        
        # Get paginated results
        query = query_base.order_by(
            desc(Booking.start_time)
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        appointments = result.scalars().all()
        
        return appointments, total
    
    async def get_appointment_stats(self) -> dict:
        """Get appointment statistics"""
        query = select(Booking)
        result = await self.db.execute(query)
        all_appointments = result.scalars().all()
        
        stats = {
            'total': len(all_appointments),
            'pending': len([a for a in all_appointments if a.status == 'PENDING']),
            'accepted': len([a for a in all_appointments if a.status == 'ACCEPTED']),
            'cancelled': len([a for a in all_appointments if a.status == 'CANCELLED']),
            'rescheduled': len([a for a in all_appointments if a.status == 'RESCHEDULED']),
        }
        return stats
    
    async def delete_appointment(self, appointment_id: UUID) -> bool:
        """Delete an appointment"""
        appointment = await self.get_appointment_by_id(appointment_id)
        if not appointment:
            return False
        
        await self.db.delete(appointment)
        await self.db.flush()
        return True
