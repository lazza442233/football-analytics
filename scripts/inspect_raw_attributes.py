import asyncio

from sqlalchemy import text

from src.database import engine


async def inspect_raw_attributes():
    async with engine.connect() as conn:
        # Check Passes for shot info
        print("--- PASS ATTRIBUTES ---")
        q = text("SELECT attributes FROM event WHERE type='Pass' LIMIT 5")
        rows = await conn.execute(q)
        for r in rows:
            print(r[0])

        # Check Carries for location info
        print("\n--- CARRY ATTRIBUTES ---")
        q_c = text("SELECT attributes FROM event WHERE type='Carry' LIMIT 5")
        rows_c = await conn.execute(q_c)
        for r in rows_c:
            print(r[0])


if __name__ == "__main__":
    asyncio.run(inspect_raw_attributes())
