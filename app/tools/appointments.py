"""
Cal.com V2 Appointment Tools
JSON Schema based tools for LLM invocation (LiveKit agents compatible)
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict
from app.integrations.calcom.client import calcom_client
from app.config.database import AsyncSessionLocal
from app.models.booking import Booking, BookingStatus

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# JSON SCHEMA TOOL DEFINITIONS (for LLM function calling)
# ═══════════════════════════════════════════════════════════════════

TOOLS_SCHEMA = [

    {
        "type": "function",
        "function": {
            "name": "get_available_slots",
            "description": """
                Get available appointment slots for the dental clinic.
                Use this when patient asks about availability, free slots,
                or wants to know when they can book an appointment.
                Always ask for preferred date before calling this.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to check availability in YYYY-MM-DD format. Example: '2024-08-13'"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Patient's timezone. Default is 'Asia/Kolkata'",
                        "default": "Asia/Kolkata"
                    }
                },
                "required": ["date"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": """
                Book a dental appointment for a patient.
                Use this when patient confirms they want to book an appointment.
                You MUST collect name, email, and start time before calling.
                Phone number is optional but recommended.
                Start time must be from available slots only.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Appointment start time in ISO 8601 UTC format. Example: '2024-08-13T09:00:00Z'"
                    },
                    "name": {
                        "type": "string",
                        "description": "Patient's full name. Example: 'John Doe'"
                    },
                    "email": {
                        "type": "string",
                        "description": "Patient's email address. Example: 'john@example.com'"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Patient's phone number with country code. Example: '+919876543210'",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Patient's timezone. Default: 'Asia/Kolkata'",
                        "default": "Asia/Kolkata"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any additional notes or reason for visit"
                    }
                },
                "required": ["start", "name", "email"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_booking",
            "description": """
                Get details of an existing booking.
                Use this when patient wants to check their appointment details.
                Can search by booking UID or email address.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_uid": {
                        "type": "string",
                        "description": "Unique booking ID from Cal.com. Example: 'abc123xyz'"
                    },
                    "email": {
                        "type": "string",
                        "description": "Patient's email to find their bookings"
                    }
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": """
                Reschedule an existing appointment to a new time.
                Use this when patient wants to change their appointment time.
                You need the booking UID and new desired time.
                Always check available slots first before rescheduling.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_uid": {
                        "type": "string",
                        "description": "Unique booking ID of appointment to reschedule"
                    },
                    "new_start": {
                        "type": "string",
                        "description": "New appointment time in ISO 8601 UTC format. Example: '2024-08-15T10:00:00Z'"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for rescheduling"
                    }
                },
                "required": ["booking_uid", "new_start"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": """
                Cancel an existing appointment.
                Use this when patient explicitly asks to cancel their appointment.
                Always confirm with patient before cancelling.
                You need the booking UID to cancel.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_uid": {
                        "type": "string",
                        "description": "Unique booking ID of appointment to cancel"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for cancellation"
                    }
                },
                "required": ["booking_uid"]
            }
        }
    }
]


# ═══════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════

async def get_available_slots(
    date: str,
    timezone: str = "Asia/Kolkata"
) -> str:
    """Get available appointment slots"""
    try:
        logger.info(f"🗓️ Getting slots for date: {date}, timezone: {timezone}")
        
        # Add one day for end date
        start_date = date
        end_date = (
            datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        
        result = await calcom_client.get_available_slots(
            start_date=start_date,
            end_date=end_date,
            timezone=timezone
        )
        
        if result.get("status") != "success":
            return "Sorry, I couldn't fetch available slots. Please try again."
        
        slots_data = result.get("data", {})
        
        if not slots_data:
            return f"No available slots found for {date}. Would you like to check another date?"
        
        # Format slots for LLM to read
        formatted_slots = []
        for date_key, slots in slots_data.items():
            for slot in slots:
                start_time = slot.get("start", "")
                # Convert UTC to readable format
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%I:%M %p")
                formatted_slots.append(f"• {formatted_time} ({start_time})")
        
        if not formatted_slots:
            return f"No available slots for {date}. Please try another date."
        
        slots_list = "\n".join(formatted_slots[:10])  # Show max 10 slots
        return f"Available slots for {date}:\n{slots_list}\n\nWhich time works best for you?"
        
    except Exception as e:
        logger.error(f"❌ Error getting slots: {e}", exc_info=True)
        return f"Sorry, I couldn't check availability. Please try again. Error: {str(e)}"


async def book_appointment(
    start: str,
    name: str,
    email: str,
    phone: str = None,
    timezone: str = "Asia/Kolkata",
    notes: str = None,
    session_id: str = None
) -> str:
    """Book a new appointment and save to database"""
    try:
        logger.info(f"📅 Booking appointment for {name} ({email}) at {start}")
        
        # Call Cal.com V2 API
        result = await calcom_client.create_booking(
            start=start,
            name=name,
            email=email,
            timezone=timezone,
            phone=phone,
            notes=notes
        )
        
        if result.get("status") != "success":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            return f"Sorry, I couldn't book the appointment: {error_msg}"
        
        booking_data = result.get("data", {})
        booking_uid  = booking_data.get("uid")
        booking_id   = booking_data.get("id")
        start_time   = booking_data.get("start")
        end_time     = booking_data.get("end")
        
        # Save to Neon PostgreSQL database
        try:
            async with AsyncSessionLocal() as db:
                # Parse datetime strings
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt   = datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None
                
                new_booking = Booking(
                    calcom_booking_id  = booking_id,
                    calcom_booking_uid = booking_uid,
                    patient_name       = name,
                    patient_email      = email,
                    patient_phone      = phone,
                    patient_timezone   = timezone,
                    start_time         = start_dt,
                    end_time           = end_dt,
                    event_type_id      = booking_data.get("eventTypeId"),
                    duration_minutes   = booking_data.get("duration", 30),
                    status             = BookingStatus.ACCEPTED,
                    notes              = notes,
                    livekit_session_id = session_id
                )
                db.add(new_booking)
                await db.commit()
                logger.info(f"✅ Booking saved to DB: {booking_uid}")
        except Exception as db_err:
            logger.warning(f"⚠️ Failed to save booking to DB: {db_err}")
        
        # Format response for patient
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
        
        response = (
            f"Your appointment has been successfully booked! 🎉\n\n"
            f"📋 Booking Details:\n"
            f"• Name: {name}\n"
            f"• Date & Time: {formatted_time}\n"
            f"• Email: {email}\n"
        )
        
        if phone:
            response += f"• Phone: {phone}\n"
        
        response += (
            f"• Booking ID: {booking_uid}\n\n"
            f"A confirmation email will be sent to {email}. "
            f"Is there anything else I can help you with?"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error booking appointment: {e}", exc_info=True)
        return f"Sorry, I couldn't complete the booking. Please try again. Error: {str(e)}"


async def get_booking(
    booking_uid: str = None,
    email: str = None
) -> str:
    """Get booking details by UID or email"""
    try:
        if booking_uid:
            logger.info(f"🔍 Getting booking: {booking_uid}")
            result = await calcom_client.get_booking(booking_uid)
            
            if result.get("status") != "success":
                return f"No booking found with ID: {booking_uid}"
            
            data = result.get("data", {})
            return _format_booking_details(data)
        
        elif email:
            logger.info(f"🔍 Getting bookings for email: {email}")
            result = await calcom_client.get_bookings_by_email(email)
            
            if result.get("status") != "success":
                return f"No bookings found for email: {email}"
            
            bookings = result.get("data", [])
            
            if not bookings:
                return f"No appointments found for {email}."
            
            # Return most recent active booking
            active = [
                b for b in bookings
                if b.get("status") in ["accepted", "pending"]
            ]
            
            if not active:
                return f"No upcoming appointments found for {email}."
            
            # Return details of first active booking
            response = f"Found {len(active)} upcoming appointment(s) for {email}:\n\n"
            for booking in active[:3]:  # Show max 3
                response += _format_booking_details(booking) + "\n\n"
            
            return response
        
        else:
            return "Please provide a booking ID or email address to look up appointments."
        
    except Exception as e:
        logger.error(f"❌ Error getting booking: {e}", exc_info=True)
        return f"Sorry, I couldn't retrieve the booking. Error: {str(e)}"


async def reschedule_appointment(
    booking_uid: str,
    new_start: str,
    reason: str = None
) -> str:
    """Reschedule an existing appointment"""
    try:
        logger.info(f"🔄 Rescheduling booking {booking_uid} to {new_start}")
        
        result = await calcom_client.reschedule_booking(
            booking_uid=booking_uid,
            new_start=new_start,
            reason=reason
        )
        
        if result.get("status") != "success":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            return f"Sorry, I couldn't reschedule: {error_msg}"
        
        data = result.get("data", {})
        new_start_time = data.get("start", new_start)
        
        # Update database
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                stmt = select(Booking).where(
                    Booking.calcom_booking_uid == booking_uid
                )
                result_db = await db.execute(stmt)
                booking = result_db.scalar_one_or_none()
                
                if booking:
                    dt = datetime.fromisoformat(new_start_time.replace("Z", "+00:00"))
                    booking.start_time         = dt
                    booking.status             = BookingStatus.RESCHEDULED
                    booking.rescheduling_reason = reason
                    await db.commit()
                    logger.info(f"✅ Booking updated in DB: {booking_uid}")
        except Exception as db_err:
            logger.warning(f"⚠️ Failed to update DB: {db_err}")
        
        # Format response
        dt = datetime.fromisoformat(new_start_time.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
        
        return (
            f"Your appointment has been successfully rescheduled! ✅\n\n"
            f"📋 New Details:\n"
            f"• New Date & Time: {formatted_time}\n"
            f"• Booking ID: {booking_uid}\n\n"
            f"A confirmation email will be sent to you. "
            f"Is there anything else I can help you with?"
        )
        
    except Exception as e:
        logger.error(f"❌ Error rescheduling: {e}", exc_info=True)
        return f"Sorry, I couldn't reschedule the appointment. Error: {str(e)}"


async def cancel_appointment(
    booking_uid: str,
    reason: str = None
) -> str:
    """Cancel an existing appointment"""
    try:
        logger.info(f"❌ Cancelling booking: {booking_uid}")
        
        result = await calcom_client.cancel_booking(
            booking_uid=booking_uid,
            reason=reason
        )
        
        if result.get("status") != "success":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            return f"Sorry, I couldn't cancel: {error_msg}"
        
        # Update database
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                stmt = select(Booking).where(
                    Booking.calcom_booking_uid == booking_uid
                )
                result_db = await db.execute(stmt)
                booking = result_db.scalar_one_or_none()
                
                if booking:
                    booking.status              = BookingStatus.CANCELLED
                    booking.cancellation_reason = reason
                    await db.commit()
                    logger.info(f"✅ Booking cancelled in DB: {booking_uid}")
        except Exception as db_err:
            logger.warning(f"⚠️ Failed to update DB: {db_err}")
        
        return (
            f"Your appointment has been successfully cancelled. ✅\n\n"
            f"• Booking ID: {booking_uid}\n"
            f"• Status: Cancelled\n\n"
            f"We're sorry to see you go! If you'd like to book again "
            f"in the future, we're here to help. "
            f"Is there anything else I can help you with?"
        )
        
    except Exception as e:
        logger.error(f"❌ Error cancelling: {e}", exc_info=True)
        return f"Sorry, I couldn't cancel the appointment. Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# TOOL DISPATCHER - LLM calls this automatically
# ═══════════════════════════════════════════════════════════════════

async def execute_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    session_id: str = None
) -> str:
    """
    Main dispatcher - LLM calls this with tool name and arguments
    
    Usage in agent:
        result = await execute_tool("book_appointment", {
            "start": "2024-08-13T09:00:00Z",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+919876543210"
        })
    """
    
    TOOL_MAP = {
        "get_available_slots":  get_available_slots,
        "book_appointment":     book_appointment,
        "get_booking":          get_booking,
        "reschedule_appointment": reschedule_appointment,
        "cancel_appointment":   cancel_appointment,
    }
    
    tool_func = TOOL_MAP.get(tool_name)
    
    if not tool_func:
        logger.warning(f"⚠️ Unknown tool: {tool_name}")
        return f"Unknown tool: {tool_name}"
    
    logger.info(f"🔧 Executing tool: {tool_name} with args: {tool_args}")
    
    # Add session_id for booking tracking
    if tool_name == "book_appointment" and session_id:
        tool_args["session_id"] = session_id
    
    return await tool_func(**tool_args)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _format_booking_details(data: Dict) -> str:
    """Format booking data into readable string for LLM"""
    booking_uid = data.get("uid", "N/A")
    status      = data.get("status", "N/A")
    start       = data.get("start", "N/A")
    
    # Format time
    try:
        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        formatted_time = start
    
    # Get attendee info
    attendees = data.get("attendees", [])
    attendee  = attendees[0] if attendees else {}
    name      = attendee.get("name", "N/A")
    email     = attendee.get("email", "N/A")
    phone     = attendee.get("phoneNumber", None)
    
    result = (
        f"📋 Appointment Details:\n"
        f"• Patient: {name}\n"
        f"• Email: {email}\n"
    )
    
    if phone:
        result += f"• Phone: {phone}\n"
    
    result += (
        f"• Date & Time: {formatted_time}\n"
        f"• Status: {status}\n"
        f"• Booking ID: {booking_uid}"
    )
    
    return result