#!/usr/bin/env python
"""Audit database contents."""

import asyncio

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import engine
from src.models import Competition, Event, Match, Player


async def audit():
    async with AsyncSession(engine) as session:
        comps = (await session.exec(select(Competition))).all()
        print("=== COMPETITIONS ===")
        for c in comps:
            print(f"  {c.id}: {c.name} ({c.gender})")

        print("\n=== MATCHES BY SEASON ===")
        result = await session.exec(
            select(
                col(Match.competition_id),
                col(Match.season_id),
                func.count(col(Match.id)).label("total"),
                func.count(col(Match.events_ingested_at)).label("with_events"),
            ).group_by(col(Match.competition_id), col(Match.season_id))
        )
        for row in result:
            print(
                f"  Comp {row[0]}, Season {row[1]}: "
                f"{row[3]}/{row[2]} matches with events"
            )

        event_count = (await session.exec(select(func.count(col(Event.id))))).one()
        print(f"\n=== TOTAL EVENTS: {event_count:,} ===")

        player_count = (await session.exec(select(func.count(col(Player.id))))).one()
        print(f"=== TOTAL PLAYERS: {player_count:,} ===")

        print("\n=== TOP EVENT TYPES ===")
        result = await session.exec(
            select(Event.type, func.count(col(Event.id)))
            .group_by(Event.type)
            .order_by(func.count(col(Event.id)).desc())
            .limit(10)
        )
        for etype, count in result:
            print(f"  {etype}: {count:,}")


if __name__ == "__main__":
    asyncio.run(audit())
