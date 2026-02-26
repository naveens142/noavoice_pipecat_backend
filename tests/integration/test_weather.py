import asyncio
from app.tools.external_tools import get_weather

async def main():
    result = await get_weather("New Delhi", "IN")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())