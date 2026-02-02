import logging
import math
import uuid
from typing import Any, Dict, List

import pandas as pd
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
        competition_id: int = 9,
        season_id: int = 281,
        team_name: str = "Bayer Leverkusen",
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
            comps: Any = sb.competitions()
            comp_df = comps[(comps['competition_id'] == self.competition_id) & (
                comps['season_id'] == self.season_id)]

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
            matches: Any = sb.matches(
                competition_id=self.competition_id, season_id=self.season_id)

            target_matches = matches[
                (matches['home_team'] == self.team_name) | (
                    matches['away_team'] == self.team_name)
            ]

            if target_matches.empty:
                logger.warning(f"No matches found for {self.team_name}.")
                return None

            target_match_row = target_matches.iloc[0]
            match_id = int(target_match_row['match_id'])
            logger.info(
                f"Targeting Match ID: {match_id} "
                f"({target_match_row['home_team']} vs {target_match_row['away_team']})"
            )

            match_obj = Match(
                id=match_id,
                competition_id=competition.id,
                match_date=pd.to_datetime(
                    target_match_row['match_date']).date(),
                home_team=str(target_match_row['home_team']),
                away_team=str(target_match_row['away_team']),
                home_score=int(target_match_row['home_score']),
                away_score=int(target_match_row['away_score'])
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
            events: Any = sb.events(match_id=match_id)

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

                # Save Events (using add_all for performance,
                # assuming clean state needed later)
                session.add_all(event_objects)
                await session.commit()

        except Exception as e:
            logger.error(f"Error ingesting events: {e}")
            raise e
