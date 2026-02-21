"""
Complete Booking Helpers

Supports:

✔ future validation
✔ slot validation
✔ booking validation
✔ reschedule validation
✔ cancel validation
✔ suggest next free slot
"""

import logging
from datetime import datetime, timezone, timedelta

from app.integrations.calcom.client import calcom_client


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════
# COMMON
# ═══════════════════════════════════════


def parse_utc(iso_utc: str):

    return datetime.fromisoformat(

        iso_utc.replace("Z", "+00:00")

    )


def now_utc():

    return datetime.now(timezone.utc)


# ═══════════════════════════════════════
# 1. FUTURE VALIDATION
# ═══════════════════════════════════════


def is_future_datetime(iso_utc: str):

    try:

        return parse_utc(iso_utc) > now_utc()

    except:

        return False


# ═══════════════════════════════════════
# 2. SLOT AVAILABLE
# ═══════════════════════════════════════


async def is_slot_available(

    iso_utc: str,
    timezone_str: str

):

    try:

        dt = parse_utc(iso_utc)

        date = dt.strftime("%Y-%m-%d")

        result = await calcom_client.get_available_slots(

            start_date=date,
            end_date=date,
            timezone=timezone_str

        )

        if result.get("status") != "success":

            return False


        slots = result.get("data", {})


        for day in slots.values():

            for slot in day:

                if slot["start"] == iso_utc:

                    return True


        return False

    except Exception as e:

        logger.error(e)

        return False


# ═══════════════════════════════════════
# 3. BOOK VALIDATION
# ═══════════════════════════════════════


async def validate_booking(

    iso_utc,
    timezone

):

    if not is_future_datetime(iso_utc):

        return False, "Cannot book past time"


    available = await is_slot_available(

        iso_utc,
        timezone

    )


    if not available:

        return False, "Slot not available"


    return True, "OK"


# ═══════════════════════════════════════
# 4. RESCHEDULE VALIDATION
# ═══════════════════════════════════════


async def validate_reschedule(

    booking_uid,
    new_iso,
    timezone

):

    try:

        booking = await calcom_client.get_booking(

            booking_uid

        )


        if booking.get("status") != "success":

            return False, "Booking not found"


        if not is_future_datetime(new_iso):

            return False, "New time must be future"


        available = await is_slot_available(

            new_iso,
            timezone

        )


        if not available:

            return False, "New slot unavailable"


        return True, "OK"


    except Exception as e:

        logger.error(e)

        return False, "Reschedule failed"


# ═══════════════════════════════════════
# 5. CANCEL VALIDATION
# ═══════════════════════════════════════


async def validate_cancel(

    booking_uid

):

    try:

        booking = await calcom_client.get_booking(

            booking_uid

        )


        if booking.get("status") != "success":

            return False, "Booking not found"


        start = booking["data"]["start"]


        if not is_future_datetime(start):

            return False, "Cannot cancel past booking"


        return True, "OK"


    except Exception as e:

        logger.error(e)

        return False, "Cancel failed"


# ═══════════════════════════════════════
# 6. AUTO SUGGEST NEXT SLOT
# ═══════════════════════════════════════


async def suggest_next_slot(

    timezone,

    days=7

):

    try:

        today = now_utc().date()

        end = today + timedelta(days=days)


        result = await calcom_client.get_available_slots(

            start_date=str(today),
            end_date=str(end),
            timezone=timezone

        )


        if result.get("status") != "success":

            return None


        slots = result.get("data", {})


        for day in sorted(slots.keys()):

            if slots[day]:

                return slots[day][0]["start"]


        return None


    except Exception as e:

        logger.error(e)

        return None


# ═══════════════════════════════════════
# 7. SMART VALIDATE + SUGGEST
# ═══════════════════════════════════════


async def validate_or_suggest(

    iso,
    timezone

):

    valid, msg = await validate_booking(

        iso,
        timezone

    )


    if valid:

        return True, iso, "OK"


    suggestion = await suggest_next_slot(

        timezone

    )


    if suggestion:

        return False, suggestion, "Suggested next available slot"


    return False, None, "No slots available"
