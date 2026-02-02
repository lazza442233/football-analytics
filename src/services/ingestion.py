import asyncio
import logging
import math
import uuid
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel.ext.asyncio.session import AsyncSession
from statsbombpy import sb

from src.database import engine
from src.models import Competition, Event, Match, Player

logger = logging.getLogger(__name__)

# Suppress pandas chained assignment warnings
pd.options.mode.chained_assignment = None


class StatsBombIngestionService:
    def __init__(
        self,
        competition_id: int | None = None,
        season_id: int | None = None,
        team_name: str | None = None,
    ):
        self.competition_id = competition_id
        self.season_id = season_id
        self.team_name = team_name

    def clean_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Remove NaN values and convert types for JSON serialization."""
        clean = {}
        for k, v in d.items():
            if isinstance(v, (list, dict)):
                clean[k] = v
                continue
            if isinstance(v, float) and math.isnan(v):
                continue
            if pd.isna(v):
                continue
            clean[k] = v
        return clean

    def _create_match_record(
        self,
        row: pd.Series,
        competition_id: int,
        season_id: int
    ) -> Match:
        """Helper to map a pandas row to a Match model."""
        return Match(
            id=int(row['match_id']),
            competition_id=competition_id,
            season_id=season_id,
            match_date=pd.to_datetime(row['match_date']).date(),
            home_team=str(row['home_team']),
            away_team=str(row['away_team']),
            home_score=int(row['home_score']),
            away_score=int(row['away_score'])
        )

    async def ingest_season_matches(
        self,
        competition_id: int,
        season_id: int,
        ingest_events: bool = False
    ) -> bool:
        """
        Fetch and upsert all matches for a given competition and season.
        Uses asyncio.to_thread for non-blocking I/O.
        """
        logger.info(
            f"Starting match ingestion for Comp={competition_id}, Season={season_id}")

        self.competition_id = competition_id
        self.season_id = season_id

        # 1. Fetch & Upsert Competition Metadata
        try:
            competition = await self.ingest_competition()
            if not competition:
                logger.error(
                    f"Competition {competition_id}/{season_id} not found.")
                return False
        except Exception as e:
            logger.error(f"Error fetching competition: {e}")
            raise e

        # 2. Fetch & Upsert Matches
        try:
            # Run blocking call in thread
            matches_data = await asyncio.to_thread(
                sb.matches,
                competition_id=competition_id,
                season_id=season_id
            )

            if isinstance(matches_data, pd.DataFrame):
                matches_df = matches_data
            else:
                matches_df = pd.DataFrame(matches_data)

            logger.info(f"Found {len(matches_df)} matches.")

            async with AsyncSession(engine) as session:
                for _, row in matches_df.iterrows():
                    match = self._create_match_record(
                        row, competition_id, season_id
                    )
                    await session.merge(match)

                await session.commit()

            logger.info("Matches upserted successfully.")

            if ingest_events:
                logger.info("Starting event ingestion for all matches...")
                for _, row in matches_df.iterrows():
                    match_id = int(row['match_id'])
                    try:
                        # Check existence later; trusting process for now.
                        await self.ingest_events(match_id)
                    except Exception as e:
                        logger.error(
                            f"Failed to ingest events for match {match_id}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to ingest matches: {e}")
            raise e

    async def run(self):
        logger.info("Starting ingestion...")

        # Upsert Competition
        competition = await self.ingest_competition()
        if not competition:
            return

        # Fetch Matches
        match_obj = await self.ingest_match(competition)
        if not match_obj:
            return

        # Fetch Events
        await self.ingest_events(match_obj.id)

        logger.info("Ingestion complete successfully.")

    async def ingest_competition(self) -> Competition | None:
        logger.info(f"Fetching competition {self.competition_id}...")
        try:
            comp_id = self.competition_id
            seas_id = self.season_id

            if comp_id is None or seas_id is None:
                raise ValueError("Competition ID and Season ID must be set.")

            # Non-blocking fetch
            comps = await asyncio.to_thread(sb.competitions)

            # Cast to DataFrame for type safety if needed, though usually it is one
            if not isinstance(comps, pd.DataFrame):
                comps = pd.DataFrame(comps)

            comp_df = comps[(comps['competition_id'] == comp_id) & (
                comps['season_id'] == seas_id)]

            if comp_df.empty:
                logger.warning("Competition not found.")
                return None

            comp_row = comp_df.iloc[0]
            competition = Competition(
                id=int(comp_row['competition_id']),
                name=str(comp_row['competition_name']),
                gender=str(comp_row['competition_gender'])
            )

            logger.info(f"Saving competition: {competition.name}")
            async with AsyncSession(engine) as session:
                await session.merge(competition)
                await session.commit()

            return competition
        except Exception as e:
            logger.error(f"Error ingesting competition: {e}")
            raise e

    async def ingest_match(self, competition: Competition) -> Match | None:
        logger.info(f"Fetching matches for {competition.name}...")
        try:
            comp_id = self.competition_id
            seas_id = self.season_id

            if comp_id is None or seas_id is None:
                raise ValueError("Competition ID and Season ID must be set.")

            matches: Any = await asyncio.to_thread(
                sb.matches,
                competition_id=comp_id,
                season_id=seas_id
            )

            if not isinstance(matches, pd.DataFrame):
                # statsbombpy can return dicts if credentials fail or other reasons,
                # but typically returns DF.
                logger.warning(
                    f"sb.matches returned {type(matches)}, expected DataFrame")
                # Attempt conversion if it looks like a list of dicts
                matches = pd.DataFrame(matches)

            target_matches = matches[
                (matches['home_team'] == self.team_name) | (
                    matches['away_team'] == self.team_name)
            ]

            if target_matches.empty:
                logger.warning(f"No matches found for {self.team_name}.")
                return None

            target_match_row = target_matches.iloc[0]

            match_obj = self._create_match_record(
                target_match_row, competition.id, seas_id
            )

            logger.info(
                f"Targeting Match ID: {match_obj.id} "
                f"({match_obj.home_team} vs {match_obj.away_team})"
            )

            async with AsyncSession(engine) as session:
                await session.merge(match_obj)
                await session.commit()

            return match_obj
        except Exception as e:
            logger.error(f"Error ingesting match: {e}")
            raise e

    async def ingest_events(self, match_id: int):
        logger.info(f"Fetching events for match {match_id}...")
        try:
            events: Any = await asyncio.to_thread(sb.events, match_id=match_id)

            if not isinstance(events, pd.DataFrame):
                events = pd.DataFrame(events)

            event_objects: List[Event] = []
            player_objects: Dict[int, Player] = {}

            logger.info(f"Processing {len(events)} events...")

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
                clean_attrs = self.clean_dict(row.to_dict())

                # Remove core fields as they are stored in dedicated columns
                core_fields = [
                    'id', 'match_id', 'minute', 'second', 'type',
                    'player_id', 'team_id', 'location', 'index',
                    'period', 'timestamp'
                ]
                for field in core_fields:
                    clean_attrs.pop(field, None)

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

            logger.info(
                f"Saving {len(player_objects)} players and "
                f"{len(event_objects)} events to DB..."
            )

            async with AsyncSession(engine) as session:
                # Save Players
                for p in player_objects.values():
                    await session.merge(p)
                await session.commit()

                # Save Events using Upsert (ON CONFLICT DO UPDATE) for Idempotency
                if event_objects:
                    # Convert SQLModel objects to dicts for bulk insert
                    events_data = [e.model_dump() for e in event_objects]

                    stmt = pg_insert(Event).values(events_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['id'],
                        set_=stmt.excluded
                    )
                    await session.exec(stmt)
                    await session.commit()

        except Exception as e:
            logger.error(f"Error ingesting events: {e}")
            raise e
