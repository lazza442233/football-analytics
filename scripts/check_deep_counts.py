import asyncio

from sqlalchemy import distinct, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import engine
from src.models import Event


async def check_deep_counts():
    print("Checking database deep counts...")

    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Check distinct matches in Events
        # type: ignore
        result = await session.exec(select(func.count(distinct(Event.match_id))))
        events_match_count = result.one()
        print(f"Number of matches with events: {events_match_count}")

        # Check average events per match
        result = await session.exec(
            select(Event.match_id, func.count(Event.id)).group_by(Event.match_id)  # type: ignore
        )
        counts = result.all()
        if counts:
            print(f"Sample event counts per match (first 5): {counts[:5]}")
            avg = sum(c[1] for c in counts) / len(counts)
            print(f"Average events per match: {avg:.2f}")


if __name__ == "__main__":
    asyncio.run(check_deep_counts())
