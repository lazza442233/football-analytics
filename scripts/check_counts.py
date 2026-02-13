import asyncio

from sqlalchemy import func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import engine
from src.models import Event, Match, Player


async def check_counts():
    print("Checking database counts...")

    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        match_result = await session.exec(select(func.count(Match.id)))
        match_count = match_result.one()

        event_result = await session.exec(select(func.count(Event.id)))
        event_count = event_result.one()

        player_result = await session.exec(select(func.count(Player.id)))
        player_count = player_result.one()

        print(f"Matches: {match_count}")
        print(f"Events: {event_count}")
        print(f"Players: {player_count}")


if __name__ == "__main__":
    asyncio.run(check_counts())
