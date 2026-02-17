"""Check ingestion status for a competition/season."""

import argparse
import asyncio

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import engine
from src.models import Event, Match


async def check_status(competition_id: int, season_id: int):
    """Print detailed ingestion status for a competition/season."""
    async with AsyncSession(engine) as session:
        # Get match stats
        match_result = await session.exec(
            select(func.count(col(Match.id)))
            .where(Match.competition_id == competition_id)
            .where(Match.season_id == season_id)
        )
        total_matches = match_result.one()

        completed_result = await session.exec(
            select(func.count(col(Match.id)))
            .where(Match.competition_id == competition_id)
            .where(Match.season_id == season_id)
            .where(col(Match.events_ingested_at).isnot(None))
        )
        completed_matches = completed_result.one()

        # Get event count
        event_result = await session.exec(
            select(func.count(col(Event.id))).where(
                col(Event.match_id).in_(
                    select(Match.id)
                    .where(Match.competition_id == competition_id)
                    .where(Match.season_id == season_id)
                )
            )
        )
        total_events = event_result.one()

        # Get unique player count
        player_result = await session.exec(
            select(func.count(func.distinct(Event.player_id))).where(
                col(Event.match_id).in_(
                    select(Match.id)
                    .where(Match.competition_id == competition_id)
                    .where(Match.season_id == season_id)
                )
            )
        )
        unique_players = player_result.one()

    # Calculate percentages
    completion_pct = (
        (completed_matches / total_matches * 100) if total_matches > 0 else 0
    )
    pending_matches = total_matches - completed_matches

    print("\n📊 Ingestion Status Report")
    print(f"Competition ID: {competition_id}, Season ID: {season_id}")
    print(f"{'=' * 60}")
    completed_pct = f"({completion_pct:.1f}%)"
    print(
        f"Matches:            {completed_matches}/{total_matches} completed "
        f"{completed_pct}"
    )
    print(f"Pending matches:    {pending_matches}")
    print(f"Events ingested:    {total_events:,}")
    print(f"Unique players:     {unique_players}")
    avg_events = total_events // completed_matches if completed_matches > 0 else 0
    print(f"Avg events/match:   {avg_events}")
    print(f"{'=' * 60}\n")

    if pending_matches > 0:
        print("💡 To ingest pending matches, run:")
        print(
            f"   poetry run python -m src.scripts.ingest_matches "
            f"--comp-id {competition_id} --season-id {season_id} "
            f"--events --parallel 10\n"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Check ingestion status for a competition/season"
    )
    parser.add_argument("--comp-id", type=int, required=True, help="Competition ID")
    parser.add_argument("--season-id", type=int, required=True, help="Season ID")
    args = parser.parse_args()

    asyncio.run(check_status(args.comp_id, args.season_id))


if __name__ == "__main__":
    main()
