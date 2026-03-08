"""
Booking Lookup Helpers
Production ready helper for Cal.com booking lookup

Supports:

• Find booking_uid automatically
• Cancel booking lookup
• Reschedule lookup
• Get booking lookup
• Suggest if multiple bookings

Priority:

1 session_id
2 email
3 phone

"""


from typing import Optional, List

from sqlalchemy import select, desc

from app.config.database import AsyncSessionLocal
from app.models.booking import Booking, BookingStatus


from app.config.logging import app_logger
logger = app_logger


# ═══════════════════════════════════════════
# MAIN LOOKUP FUNCTION
# ═══════════════════════════════════════════

async def find_booking(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    session_id: Optional[str] = None,
    only_future: bool = True
) -> Optional[Booking]:

    """
    Returns latest booking automatically

    Used for:

    cancel
    reschedule
    get booking

    """

    async with AsyncSessionLocal() as db:

        query = select(Booking)

        # Priority order

        if session_id:
            query = query.where(
                Booking.livekit_session_id == session_id
            )

        elif email:
            email = email.strip().lower()
            query = query.where(
                Booking.patient_email == email
            )

        elif phone:
            query = query.where(
                Booking.patient_phone == phone
            )

        else:
            return None


        # Only future bookings
        if only_future:

            from datetime import datetime, timezone

            query = query.where(
                Booking.start_time >= datetime.now(timezone.utc)
            )


        query = query.where(
            Booking.status.in_(
                [
                    BookingStatus.ACCEPTED,
                    BookingStatus.PENDING,
                    BookingStatus.RESCHEDULED
                ]
            )
        )


        query = query.order_by(desc(Booking.start_time))

        logger.info(f"DB Query for find_booking: {query}")
        result = await db.execute(query)

        booking = result.scalar_one_or_none()

        logger.info(f"DB response for find_booking: {booking}")

        return booking


# ═══════════════════════════════════════════
# GET UID ONLY
# ═══════════════════════════════════════════

async def get_booking_uid(
    email=None,
    phone=None,
    session_id=None
) -> Optional[str]:
    email = email.strip().lower()

    # Log all bookings for diagnostics
    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            all_stmt = select(Booking).where(
                Booking.patient_email == email
            ).order_by(Booking.start_time.desc())
            all_result = await db.execute(all_stmt)
            all_bookings = all_result.scalars().all()
            
            if all_bookings:
                logger.info(f"📋 All {len(all_bookings)} booking(s) for {email}:")
                for idx, b in enumerate(all_bookings, 1):
                    logger.info(
                        f"   [{idx}] UID: {b.calcom_booking_uid} | "
                        f"Start: {b.start_time} | Status: {b.status}"
                    )
    except Exception as e:
        logger.warning(f"⚠️ Failed to list bookings: {e}")

    # Get the active booking
    booking = await find_booking(
        email=email,
        phone=phone,
        session_id=session_id
    )

    if booking:
        logger.info(
            f"✅ Selected for cancel: UID={booking.calcom_booking_uid} "
            f"Status={booking.status} Start={booking.start_time.strftime('%Y-%m-%d %H:%M')}"
        )
        return booking.calcom_booking_uid
    else:
        logger.warning(f"⚠️ No active booking found for {email}")
        return None


# ═══════════════════════════════════════════
# GET FULL BOOKING DETAILS
# ═══════════════════════════════════════════

async def get_booking_details(
    email=None,
    phone=None,
    session_id=None
) -> Optional[Booking]:
    email = email.strip().lower()
    return await find_booking(
        email=email,
        phone=phone,
        session_id=session_id
    )


# ═══════════════════════════════════════════
# VALIDATE BOOKING EXISTS
# ═══════════════════════════════════════════

async def validate_booking_exists(
    email=None,
    phone=None,
    session_id=None
):
    email = email.strip().lower()
    booking = await find_booking(
        email=email,
        phone=phone,
        session_id=session_id
    )

    if not booking:

        return False, "No upcoming booking found."

    return True, booking


# ═══════════════════════════════════════════
# GET ALL BOOKINGS (optional)
# ═══════════════════════════════════════════

async def get_all_bookings(
    email=None,
    phone=None,
    session_id=None
) -> List[Booking]:
    email = email.strip().lower()
    async with AsyncSessionLocal() as db:

        query = select(Booking)

        if session_id:

            query = query.where(
                Booking.livekit_session_id == session_id
            )

        elif email:
            query = query.where(
                Booking.patient_email == email
            )

        elif phone:

            query = query.where(
                Booking.patient_phone == phone
            )

        query = query.order_by(desc(Booking.start_time))


        result = await db.execute(query)

        bookings = result.scalars().all()


        return bookings
