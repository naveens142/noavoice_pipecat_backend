import asyncio
from app.tools.appointments import execute_tool


async def test_all_tools():

    print("\n" + "="*50)
    print("1️⃣ Testing get_available_slots...")
    print("="*50)

    result = await execute_tool(
        "get_available_slots",
        {
            "date": "2026-02-19",
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
            "start": "23rd feb at 11am",

            "name": "Naveen Sharma",

            "email": "test_westack@gmail.com",

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
            "email": "test_westack@gmail.com"
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
            "email": "test_westack@gmail.com",

            "new_start": "24th feb at 10AM"
        }
    )

    print(result)



    print("\n" + "="*50)
    print("5️⃣ Testing cancel...")
    print("="*50)

    result = await execute_tool(
        "cancel_appointment",
        {
            "email": "test_westack@gmail.com"
        }
    )

    print(result)



asyncio.run(test_all_tools())
