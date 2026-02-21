import asyncio

from app.utils.datetime_helpers import parse_datetime, display


async def test_parser():

    test_cases = [

        "tomorrow at 3pm",
        "next monday morning",
        "friday afternoon",
        "august 25 at 2:30pm",
        "today at 9am",
        "next week at 5pm",
        "tuesday evening",
        "2026-02-20T05:30:00.000Z",
        "20th feb at 11AM",
        "2026-02-20T05:30:00Z",
        "20 jan at 11:10am"

    ]

    print("\n" + "="*60)
    print("TESTING DATETIME PARSER")
    print("="*60)

    timezone = "Asia/Kolkata"

    for test in test_cases:

        print(f"\nInput: '{test}'")

        date, time, iso_utc = parse_datetime(test, timezone)

        if iso_utc:

            print("Parsed successfully")

            print("Date:", date)

            print("Time:", time)

            print("UTC:", iso_utc)

            display_text = display(iso_utc, timezone)

            print("Display:", display_text)

        else:

            print("Failed")

    print("\n" + "="*60)


asyncio.run(test_parser())
