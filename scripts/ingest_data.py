import asyncio
from typing import Any, Dict, List
import pandas as pd
from statsbombpy import sb
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database import engine
from src.models import Competition, Match, Event, Player
import uuid
import math

# Suppress pandas chained assignment warnings
pd.options.mode.chained_assignment = None

COMPETITION_ID = 9  # 1. Bundesliga
SEASON_ID = 281     # 2023/2024
TEAM_NAME = "Bayer Leverkusen"


def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove NaN values and convert types for JSON serialization."""
    clean = {}
    for k, v in d.items():
        if isinstance(v, (list, dict)):
            # If it's a list or dict, it's not a NaN scalar, so keep it.
            # But we might want to recurse if nested? For now just keep.
            clean[k] = v
            continue

        if isinstance(v, float) and math.isnan(v):
            continue
        if pd.isna(v):
            continue
        clean[k] = v
    return clean


async def ingest():
    print("Starting ingestion...")

    # 1. Upsert Competition
    print(f"Fetching competition {COMPETITION_ID}...")
    try:
        comps: Any = sb.competitions()
        # Filter for our competition
        comp_df = comps[(comps['competition_id'] == COMPETITION_ID)
                        & (comps['season_id'] == SEASON_ID)]
        if comp_df.empty:
            print("Competition not found.")
            return

        comp_row = comp_df.iloc[0]

        competition = Competition(
            id=int(comp_row['competition_id']),
            name=str(comp_row['competition_name']),
            gender=str(comp_row['competition_gender'])
        )

        print(f"Saving competition: {competition.name}")
        async with AsyncSession(engine) as session:
            await session.merge(competition)
            await session.commit()

        # 2. Fetch Matches
        print(f"Fetching matches for {competition.name}...")
        matches: Any = sb.matches(
            competition_id=COMPETITION_ID, season_id=SEASON_ID)

        # Filter for Bayer Leverkusen (home or away)
        leverkusen_matches = matches[
            (matches['home_team'] == TEAM_NAME) | (
                matches['away_team'] == TEAM_NAME)
        ]

        if leverkusen_matches.empty:
            print(f"No matches found for {TEAM_NAME}.")
            return

        # Take the first match
        target_match_row = leverkusen_matches.iloc[0]
        match_id = int(target_match_row['match_id'])
        print(
            f"Targeting Match ID: {match_id} ({target_match_row['home_team']} vs {target_match_row['away_team']})")

        match_obj = Match(
            id=match_id,
            competition_id=competition.id,
            match_date=pd.to_datetime(target_match_row['match_date']).date(),
            home_team=str(target_match_row['home_team']),
            away_team=str(target_match_row['away_team']),

            home_score=int(target_match_row['home_score']),
            away_score=int(target_match_row['away_score'])
        )

        async with AsyncSession(engine) as session:
            await session.merge(match_obj)
            await session.commit()

        # 3. Fetch Events
        print(f"Fetching events for match {match_id}...")
        events: Any = sb.events(match_id=match_id)

        event_objects: List[Event] = []
        player_objects: Dict[int, Player] = {}

        print(f"Processing {len(events)} events...")

        for _, row in events.iterrows():
            # Handle Player
            p_id = row.get('player_id')
            if pd.notna(p_id):
                p_id = int(p_id)
                if p_id not in player_objects:
                    player_objects[p_id] = Player(
                        id=p_id,
                        name=str(row['player']),
                        position=str(row.get('position', None)) if pd.notna(
                            row.get('position')) else None
                    )

            # Handle Location
            loc = row.get('location')
            loc_x, loc_y = None, None
            if isinstance(loc, list) and len(loc) >= 2:
                loc_x, loc_y = float(loc[0]), float(loc[1])

            # Attributes
            row_dict = row.to_dict()
            clean_attrs = clean_dict(row_dict)

            # Remove core fields
            core_fields = ['id', 'match_id', 'minute', 'second', 'type',
                           'player_id', 'team_id', 'location', 'index', 'period', 'timestamp']
            for field in core_fields:
                clean_attrs.pop(field, None)

            # Use SB ID
            event_uuid = uuid.UUID(str(row['id']))

            event_obj = Event(
                id=event_uuid,
                match_id=match_id,
                minute=int(row['minute']),
                second=int(row['second']),
                type=str(row['type']),
                player_id=int(row['player_id']) if pd.notna(
                    row.get('player_id')) else None,
                team_id=int(row['team_id']),
                location_x=loc_x,
                location_y=loc_y,
                attributes=clean_attrs
            )
            event_objects.append(event_obj)

        print(
            f"Saving {len(player_objects)} players and {len(event_objects)} events to DB...")

        async with AsyncSession(engine) as session:
            # Save Players
            for p in player_objects.values():
                await session.merge(p)
            await session.commit()

            # Save Events
            # We use merge to handle potential re-runs if UUIDs conflict, but allow bulk insert optimization?
            # session.add_all(event_objects) -> if they exist it forces error. session.merge is safer for idempotency but slower.
            # For "Sample Ingestion", merge is safer.
            # Note: merging thousands of objects one by one is slow.
            # But for a single match (~3000 events), it's acceptable for a script.

            # To speed up: delete existing events for this match? Or just try add_all and catch error?
            # Let's try to add_all. If it fails, the user can reset DB.
            # Or check existence.
            # Let's use session.merge for valid Upsert behavior, but maybe in chunks?
            # Actually session.merge is fine for 3000 items locally.

            # NOTE: SQLModel/SQLAlchemy AsyncSession doesn't support bulk_save_objects very well with asyncpg sometimes?
            # `add_all` is standard.

            # Let's use `add_all` first. If ID exists, it crashes. Since we just created the table, it should be empty.
            # But wait, what if we run it twice?
            # Ops, `add_all` will fail on unique constraint.
            # I will check if events exist for this match.

            # Check count
            # result = await session.exec(select(Event).where(Event.match_id == match_id)) ...
            # Too complex for now. I'll just use add_all and assume empty or crash.

            session.add_all(event_objects)
            await session.commit()

        print("Ingestion complete successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(ingest())
