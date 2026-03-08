"""
Cal.com V2 Appointment Tools
JSON Schema based tools for LLM invocation
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict
from app.integrations.calcom.client import calcom_client
from app.config.database import AsyncSessionLocal
from app.models.booking import Booking, BookingStatus
from app.utils.booking_helpers import validate_or_suggest, validate_cancel, validate_reschedule,validate_booking
from app.utils.booking_lookup_helpers import get_booking_uid
from app.utils.datetime_helpers import parse_datetime, normalize_to_utc
from app.config.logging import app_logger
from app.tools.tools_schemas import BOOKING_TOOLS_SCHEMA

logger = app_logger


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
        # end_date = (
        #     datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
        # ).strftime("%Y-%m-%d")
        
        logger.info(f"🗓️ get_available_slots method start date: {start_date}")
        result = await calcom_client.get_available_slots(
            start_date=start_date,
            end_date=start_date,
            timezone=timezone
        )
        
        logger.info(f"🗓️ get_available_slots calcom results: {result}")
                    
        if result.get("status") != "success":
            logger.info(f"Sorry, I couldn't fetch available slots. Please try again.")
            return "Sorry, I couldn't fetch available slots. Please try again."
        
        slots_data = result.get("data", {})
        
        if not slots_data:
            logger.info(f"No available slots found for {date}. Would you like to check another date?")
            return f"No available slots found for {date}. Would you like to check another date?"
        
        # Format slots for LLM to read (filter to 30-minute intervals)
        formatted_slots = []
        for date_key, slots in slots_data.items():
            for slot in slots:
                start_time = slot.get("start", "")
                # Convert UTC to readable format
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                # Filter to show only 30-minute intervals (minutes must be :00 or :30)
                if dt.minute % 30 == 0:
                    formatted_time = dt.strftime("%I:%M %p")
                    formatted_slots.append(f"• {formatted_time} ({start_time})")
        
        if not formatted_slots:
            logger.info(f"No available slots for {date}. Please try another date")
            return f"No available slots for {date}. Please try another date."
        
        slots_list = "\n".join(formatted_slots[:10])  # Show max 10 slots
        logger.info(f"Available slots for {date}:\n{slots_list}\n\nWhich time works best for you?")
        return f"Available slots for {date}:\n{slots_list}\n\nWhich time works best for you?"
        
    except Exception as e:
        logger.error(f"❌ Error getting slots: {e}", exc_info=True)
        return f"Sorry, I couldn't check availability. Please try again. Error: {str(e)}"


async def book_appointment(
    datetime_natural: str,
    name: str,
    email: str,
    phone: str = None,
    timezone: str = "Asia/Kolkata",
    notes: str = None,
    session_id: str = None
) -> str:
    """Book a new appointment and save to database"""
    try:
        start = datetime_natural
        logger.info(f"Booking request: {start}")

        # ✅ STEP 1: parse natural language → ISO UTC

        date, time, iso_utc = parse_datetime(start, timezone)
        start= iso_utc

        if not iso_utc:

            return "Sorry, I couldn't understand the date and time. Please try again."


        logger.info(f"Parsed ISO: {iso_utc}")

        email=email.strip().lower()
        name=name.strip().lower()
        logger.info(f"📅 Booking appointment for {name} ({email}) at {start}")

        # validate booking 
        valid, msg  = await validate_booking(start,timezone)
        if not valid:
            logger.info(f"📅 Booking appointment validation failed for {name} reason: {msg}")
            return {

                "status": "failed"
            }
                
        logger.info(f"📅 create_booking {name} ({email}) at {start}")
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
                logger.info(f"start_time: {start_time}")
                logger.info(f"end_time: {end_time}")

                logger.info(f"end_time: {end_time}")
                logger.info(f"end_dt: {end_dt}")

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
    email: str
) -> str:
    """Get booking details by UID or email"""
    try:
        email=email.strip().lower()
        booking_uid = await get_booking_uid(email=email)

        if not booking_uid:
            return "No booking found."
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
                if b.get("status") in ["ACCEPTED", "PENDING"]
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
        email: str,
    new_start: str,
    reason: str = None,
    timezone: str = "Asia/Kolkata",
) -> str:
    """Reschedule an existing appointment"""
    try:
        # ✅ STEP 1: parse natural language → ISO UTC
        parsed_time, time, iso_utc = parse_datetime(new_start, timezone)

        if not iso_utc:

            return "Sorry, I couldn't understand the date and time. Please try again."


        logger.info(f"Parsed ISO: {iso_utc}")

        email=email.strip().lower()
        booking_uid = await get_booking_uid(email=email)
        if not booking_uid:
            return "No upcoming booking found to reschedule."
        
        logger.info(f"🔄 Rescheduling booking {booking_uid} to {parsed_time}")

        valid, msg = await validate_reschedule(booking_uid, iso_utc, timezone)
        if not valid:
            logger.info(f"📅 Rescheduling appointment validation failed for {booking_uid}  reason:{msg}")
            return msg
        
        result = await calcom_client.reschedule_booking(
            booking_uid=booking_uid,
            new_start=iso_utc,
            reason=reason
        )
        
        if result.get("status") != "success":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            return f"Sorry, I couldn't reschedule: {error_msg}"
        
        data = result.get("data", {})
        new_start_time = data.get("start", new_start)
        
        # 🔑 CRITICAL: Extract the NEW booking UID from Cal.com's reschedule response
        # Cal.com returns rescheduledToUid which is the NEW booking UID
        new_booking_uid = data.get("rescheduledToUid") or data.get("uid")
        
        if not new_booking_uid:
            logger.error(f"❌ Cal.com response missing new booking UID. Response: {data}")
            # If we can't get new UID, at least log the issue
            new_booking_uid = booking_uid
        else:
            logger.info(f"✅ Got new booking UID from reschedule: {new_booking_uid}")
        
        # 🔑 CRITICAL: Update database with NEW booking UID
        # This ensures cancel operations use the correct UID
        update_successful = False
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, update, text
                
                # First, try to find by old UID
                stmt = select(Booking).where(
                    Booking.calcom_booking_uid == booking_uid
                )
                result_db = await db.execute(stmt)
                booking = result_db.scalar_one_or_none()
                
                if not booking:
                    # If not found by UID, search by email + patient info (fallback)
                    logger.warning(f"⚠️ Booking not found by UID {booking_uid}, searching by email {email}")
                    stmt = select(Booking).where(
                        Booking.patient_email == email,
                        Booking.status.in_([BookingStatus.ACCEPTED, BookingStatus.PENDING, BookingStatus.RESCHEDULED])
                    ).order_by(Booking.start_time.desc())
                    result_db = await db.execute(stmt)
                    booking = result_db.scalars().first()
                
                if booking:
                    dt = datetime.fromisoformat(new_start_time.replace("Z", "+00:00"))
                    old_uid = booking.calcom_booking_uid
                    old_start = booking.start_time
                    booking_id = booking.id
                    
                    logger.info(f"🔍 Found booking to update: ID={booking_id}, old_uid={old_uid}")
                    
                    # 🔑 Use raw SQL UPDATE for maximum reliability and control
                    raw_update = text("""
                        UPDATE tbl_bookings 
                        SET calcom_booking_uid = :new_uid,
                            start_time = :new_start,
                            status = :new_status,
                            rescheduling_reason = :reason
                        WHERE id = :booking_id
                    """)
                    
                    result = await db.execute(raw_update, {
                        'new_uid': new_booking_uid,
                        'new_start': dt,
                        'new_status': BookingStatus.RESCHEDULED,
                        'reason': reason,
                        'booking_id': booking_id
                    })
                    logger.info(f"🔄 Raw SQL UPDATE executed: {result.rowcount} row(s) affected")
                    
                    # Flush and commit
                    await db.flush()
                    await db.commit()
                    logger.info(f"✅ Database commit completed - waiting for verification")
                    
                    # Critical: Use a completely new session for verification
                    # This ensures we read from the database, not the session cache
                    await db.close()
                    
                    # New session for verification
                    async with AsyncSessionLocal() as verify_db:
                        verify_stmt = select(Booking).where(Booking.id == booking_id)
                        verify_result = await verify_db.execute(verify_stmt)
                        updated_booking = verify_result.scalar_one_or_none()
                        
                        if updated_booking and updated_booking.calcom_booking_uid == new_booking_uid:
                            logger.info(
                                f"✅ Booking VERIFIED updated in DB:\n"
                                f"   Booking ID: {booking_id}\n"
                                f"   Old UID: {old_uid} @ {old_start}\n"
                                f"   New UID: {updated_booking.calcom_booking_uid} @ {updated_booking.start_time}\n"
                                f"   Status: {updated_booking.status}"
                            )
                            update_successful = True
                        else:
                            actual_uid = updated_booking.calcom_booking_uid if updated_booking else "NOT FOUND"
                            actual_status = updated_booking.status if updated_booking else "N/A"
                            logger.error(
                                f"❌ VERIFICATION FAILED:\n"
                                f"   Booking ID: {booking_id}\n"
                                f"   Expected UID: {new_booking_uid}\n"
                                f"   Actual UID: {actual_uid}\n"
                                f"   Status: {actual_status}\n"
                                f"   This means the raw SQL UPDATE didn't work!"
                            )
                else:
                    logger.error(f"❌ Booking not found for email {email} or UID {booking_uid}")
        except Exception as db_err:
            logger.error(f"❌ Database update exception: {db_err}", exc_info=True)
        
        # Format response
        dt = datetime.fromisoformat(new_start_time.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
        
        return (
            f"Your appointment has been successfully rescheduled! ✅\n\n"
            f"📋 New Details:\n"
            f"• New Date & Time: {formatted_time}\n"
            f"• Booking ID: {new_booking_uid}\n\n"
            f"A confirmation email will be sent to you. "
            f"Is there anything else I can help you with?"
        )
        
    except Exception as e:
        logger.error(f"❌ Error rescheduling: {e}", exc_info=True)
        return f"Sorry, I couldn't reschedule the appointment. Error: {str(e)}"


async def cancel_appointment(
    email: str,
    reason: str = None
) -> str:
    """Cancel an existing appointment"""
    try:
        email=email.strip().lower()
        booking_uid = await get_booking_uid(email=email)

        if not booking_uid:
            return "No upcoming booking found to cancel."
        
        logger.info(f"❌ Attempting to cancel booking: {booking_uid}")

        valid, msg = await validate_cancel(booking_uid)
        if not valid:
            logger.info(f"📅 Cancelling appointment validation failed for {booking_uid}: {msg}")
            return msg
        
        logger.info(f"✅ Booking validation passed, proceeding with cancellation")
        
        # Cal.com requires cancellation reason when host is cancelling
        if not reason:
            reason = "Cancelled by user"
        
        logger.info(f"📞 Calling Cal.com API to cancel: {booking_uid}")
        result = await calcom_client.cancel_booking(
            booking_uid=booking_uid,
            reason=reason
        )
        
        logger.info(f"📞 Cal.com responded with status: {result.get('status')}")
        
        if result.get("status") != "success":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            logger.error(f"❌ Cal.com rejection: {error_msg}")
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
                else:
                    logger.warning(f"⚠️ Booking not found in DB for UID: {booking_uid}")
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
        logger.error(f"❌ Error during cancel operation: {e}", exc_info=True)
        
        # Extract meaningful error message from Cal.com
        error_msg = str(e)
        if "already been cancelled" in error_msg or "already cancelled" in error_msg.lower():
            return (
                f"❌ This appointment is already cancelled.\n\n"
                f"The booking has already been cancelled (likely during a reschedule operation).\n"
                f"If you need to extend or rebook, please create a new appointment."
            )
        elif "Bad Request" in error_msg or "400" in error_msg:
            # Try to extract the original Cal.com error message
            try:
                import json
                if "Cal.com API error" in error_msg:
                    # Parse the error to extract useful info
                    if "{" in error_msg:
                        json_start = error_msg.rfind("{")
                        json_end = error_msg.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            error_data = json.loads(error_msg[json_start:json_end])
                            cal_error = error_data.get("error", {}).get("message", error_msg)
                            logger.error(f"Cal.com error details: {cal_error}")
                            return f"❌ Cannot cancel this appointment: {cal_error}"
            except Exception as parse_error:
                logger.warning(f"⚠️ Failed to parse Cal.com error details: {parse_error}")
            return f"❌ Invalid request to cancel appointment. Please verify the booking details."
        
        return f"❌ Unexpected error cancelling appointment: {error_msg}"


# ═══════════════════════════════════════════════════════════════════
# TOOL DISPATCHER - LLM calls this automatically
# ═══════════════════════════════════════════════════════════════════

async def execute_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    session_id: str = None
) -> str:

    """
    Main dispatcher for LiveKit agent tool execution
    """

    try:

        # ✅ normalize email if present
        if "email" in tool_args and tool_args["email"]:
            tool_args["email"] = tool_args["email"].strip().lower()

        # ✅ Remove booking_uid if LLM tries to send it
        # We will fetch booking_uid internally using email + session
        tool_args.pop("booking_uid", None)

        # ✅ inject session_id automatically
        if session_id:

            tool_args["session_id"] = session_id


        TOOL_MAP = {

            "get_available_slots": get_available_slots,

            "book_appointment": book_appointment,

            "get_booking": get_booking,

            "reschedule_appointment": reschedule_appointment,

            "cancel_appointment": cancel_appointment,

        }


        tool_func = TOOL_MAP.get(tool_name)


        if not tool_func:

            logger.warning(f"Unknown tool: {tool_name}")

            return "Sorry, I cannot perform that action."


        logger.info(f"Executing tool: {tool_name}")
        logger.info(f"Args: {tool_args}")


        result = await tool_func(**tool_args)


        return result


    except Exception as e:

        logger.error(f"Tool execution error: {e}", exc_info=True)

        return "Something went wrong while processing your request."


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