import asyncio
from datetime import datetime
from app.tools.tools_dispatcher import execute_tool


async def test_all_tools():
    # Generate unique email for each test run to avoid multiple bookings conflict
    test_email = f"test_westack+1772950136@gmail.com"

    print("\n" + "="*50)
    print("1️⃣ Testing get_available_slots...")
    print("="*50)

    result = await execute_tool(
        "get_available_slots",
        {
            "date": "2026-03-11",
            "timezone": "Asia/Kolkata"
        }
    )

    print(result)



    print("\n" + "="*50)
    print("2️⃣ Testing book_appointment (NEW METHOD)...")
    print("="*50)

    result = await execute_tool(
        "book_appointment",
        {

            # ✅ CHANGED HERE
            "datetime_natural": "11h march at 11am",

            "name": "Mohit rana",

            "email": test_email,

            "phone": "+919876543210",

            "notes": "Tooth pain"
        }
    )

    print(result)



    print("\n" + "="*50)
    print("3️⃣ Testing get_booking...")
    print("="*50)

    result = await execute_tool(
        "get_booking",
        {
            "email": test_email
        }
    )

    print(result)



    print("\n" + "="*50)
    print("4️⃣ Testing reschedule...")
    print("="*50)

    result = await execute_tool(
        "reschedule_appointment",
        {

            # only email needed now
            "email": test_email,

            "new_start": "15th march at 1PM"
        }
    )

    print(result)



    print("\n" + "="*50)
    print("5️⃣ Testing cancel...")
    print("="*50)

    result = await execute_tool(
        "cancel_appointment",
        {
            "email": test_email
        }
    )

    print(result)



asyncio.run(test_all_tools())
