import asyncio
import logging
import math
import uuid
from asyncio import Semaphore, gather
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import col, select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from statsbombpy import sb

from src.database import engine
from src.models import Competition, Event, Match, Player

logger = logging.getLogger(__name__)

# Suppress pandas chained assignment warnings
pd.options.mode.chained_assignment = None

# Global lock to serialize StatsBomb API calls
# (prevents segfault with concurrent requests)
_statsbomb_api_lock: asyncio.Lock | None = None


def _get_api_lock() -> asyncio.Lock:
    """Get or create the global API lock (must be called within event loop)."""
    global _statsbomb_api_lock
    if _statsbomb_api_lock is None:
        _statsbomb_api_lock = asyncio.Lock()
    return _statsbomb_api_lock


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
        self, row: pd.Series, competition_id: int, season_id: int
    ) -> Match:
        """Helper to map a pandas row to a Match model."""
        return Match(
            id=int(row["match_id"]),
            competition_id=competition_id,
            season_id=season_id,
            match_date=pd.to_datetime(row["match_date"]).date(),
            home_team=str(row["home_team"]),
            away_team=str(row["away_team"]),
            home_score=int(row["home_score"]),
            away_score=int(row["away_score"]),
        )

    async def ingest_season_matches(
        self,
        competition_id: int,
        season_id: int,
        ingest_events: bool = False,
        max_concurrency: int = 10,
        skip_completed: bool = True,
    ) -> bool:
        """
        Fetch and upsert all matches for a given competition and season.
        Uses asyncio.to_thread for non-blocking I/O.

        Args:
            competition_id: StatsBomb competition ID
            season_id: StatsBomb season ID
            ingest_events: If True, also ingest all events for each match
            max_concurrency: Number of matches to process in parallel (default: 10)
            skip_completed: If True, skip matches already ingested (default: True)

        Returns:
            True if successful, False if competition not found
        """
        logger.info(
            f"Starting match ingestion for Comp={competition_id}, Season={season_id} "
            f"(concurrency={max_concurrency}, skip_completed={skip_completed})"
        )

        self.competition_id = competition_id
        self.season_id = season_id

        # 1. Fetch & Upsert Competition Metadata
        try:
            competition = await self.ingest_competition()
            if not competition:
                logger.error(f"Competition {competition_id}/{season_id} not found.")
                return False
        except Exception as e:
            logger.error(f"Error fetching competition: {e}")
            raise e

        # 2. Fetch & Upsert Matches
        try:
            # Run blocking call in thread (with lock for thread-safety)
            async with _get_api_lock():
                matches_data = await asyncio.to_thread(
                    sb.matches, competition_id=competition_id, season_id=season_id
                )

            if isinstance(matches_data, pd.DataFrame):
                matches_df = matches_data
            else:
                matches_df = pd.DataFrame(matches_data)

            logger.info(f"Found {len(matches_df)} matches.")

            async with AsyncSession(engine) as session:
                for _, row in matches_df.iterrows():
                    match = self._create_match_record(row, competition_id, season_id)
                    await session.merge(match)

                await session.commit()

            logger.info("Matches upserted successfully.")

            if ingest_events:
                # Determine which matches need event ingestion
                if skip_completed:
                    async with AsyncSession(engine) as session:
                        result = await session.exec(
                            select(Match.id)
                            .where(Match.competition_id == competition_id)
                            .where(Match.season_id == season_id)
                            .where(col(Match.events_ingested_at).is_(None))
                        )
                        pending_match_ids = list(result.all())

                        skipped = len(matches_df) - len(pending_match_ids)
                        logger.info(
                            f"Found {len(pending_match_ids)} pending matches "
                            f"(skipping {skipped} completed)"
                        )
                else:
                    # Process all matches
                    pending_match_ids = [
                        int(row["match_id"]) for _, row in matches_df.iterrows()
                    ]
                    logger.info(
                        f"Processing all {len(pending_match_ids)} matches "
                        f"(skip_completed=False)"
                    )

                if not pending_match_ids:
                    logger.info("No matches to ingest - all already completed!")
                    return True

                # Parallel event ingestion with bounded concurrency
                logger.info(
                    f"Starting parallel event ingestion "
                    f"(concurrency={max_concurrency})..."
                )
                semaphore = Semaphore(max_concurrency)

                async def bounded_ingest(match_id: int):
                    """Process one match with bounded concurrency."""
                    async with semaphore:
                        try:
                            logger.info(f"Ingesting events for match {match_id}...")
                            await self.ingest_events(match_id)
                            logger.info(f"✓ Completed match {match_id}")
                        except Exception as e:
                            logger.error(
                                f"✗ Failed to ingest events for match {match_id}: {e}"
                            )
                            # Don't re-raise - allow other matches to continue

                # Execute all ingestions in parallel with bounded concurrency
                await gather(*[bounded_ingest(mid) for mid in pending_match_ids])

                logger.info(
                    f"Completed event ingestion for {len(pending_match_ids)} matches"
                )

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

            # Non-blocking fetch (with lock for thread-safety)
            async with _get_api_lock():
                comps = await asyncio.to_thread(sb.competitions)

            # Cast to DataFrame for type safety if needed, though usually it is one
            if not isinstance(comps, pd.DataFrame):
                comps = pd.DataFrame(comps)

            comp_df = comps[
                (comps["competition_id"] == comp_id) & (comps["season_id"] == seas_id)
            ]

            if comp_df.empty:
                logger.warning("Competition not found.")
                return None

            comp_row = comp_df.iloc[0]
            competition = Competition(
                id=int(comp_row["competition_id"]),
                name=str(comp_row["competition_name"]),
                gender=str(comp_row["competition_gender"]),
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

            async with _get_api_lock():
                matches: Any = await asyncio.to_thread(
                    sb.matches, competition_id=comp_id, season_id=seas_id
                )

            if not isinstance(matches, pd.DataFrame):
                # statsbombpy can return dicts if credentials fail or other reasons,
                # but typically returns DF.
                logger.warning(
                    f"sb.matches returned {type(matches)}, expected DataFrame"
                )
                # Attempt conversion if it looks like a list of dicts
                matches = pd.DataFrame(matches)

            target_matches = matches[
                (matches["home_team"] == self.team_name)
                | (matches["away_team"] == self.team_name)
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
            # Use lock to serialize StatsBomb API calls (prevents segfault)
            async with _get_api_lock():
                events: Any = await asyncio.to_thread(sb.events, match_id=match_id)

            if not isinstance(events, pd.DataFrame):
                events = pd.DataFrame(events)

            event_objects: List[Event] = []
            player_objects: Dict[int, Player] = {}

            logger.info(f"Processing {len(events)} events...")

            for _, row in events.iterrows():
                # Handle Player
                p_id = row.get("player_id")
                if pd.notna(p_id):
                    p_id = int(p_id)
                    if p_id not in player_objects:
                        player_objects[p_id] = Player(
                            id=p_id,
                            name=str(row["player"]),
                            position=str(row.get("position", None))
                            if pd.notna(row.get("position"))
                            else None,
                        )

                # Handle Location
                loc = row.get("location")
                loc_x, loc_y = None, None
                if isinstance(loc, list) and len(loc) >= 2:
                    loc_x, loc_y = float(loc[0]), float(loc[1])

                # Attributes
                clean_attrs = self.clean_dict(row.to_dict())

                # Remove core fields as they are stored in dedicated columns
                core_fields = [
                    "id",
                    "match_id",
                    "minute",
                    "second",
                    "type",
                    "player_id",
                    "team_id",
                    "location",
                    "index",
                    "period",
                    "timestamp",
                ]
                for field in core_fields:
                    clean_attrs.pop(field, None)

                event_uuid = uuid.UUID(str(row["id"]))

                event_obj = Event(
                    id=event_uuid,
                    match_id=match_id,
                    minute=int(row["minute"]),
                    second=int(row["second"]),
                    type=str(row["type"]),
                    player_id=int(row["player_id"])
                    if pd.notna(row.get("player_id"))
                    else None,
                    team_id=int(row["team_id"]),
                    location_x=loc_x,
                    location_y=loc_y,
                    attributes=clean_attrs,
                )
                event_objects.append(event_obj)

            # Deduplicate by ID within the batch to avoid "Cardinality violation"
            # in ON CONFLICT if the source data contains duplicates.
            unique_events = {e.id: e for e in event_objects}
            event_objects = list(unique_events.values())

            logger.info(
                f"Saving {len(player_objects)} players and "
                f"{len(event_objects)} events to DB..."
            )

            async with AsyncSession(engine) as session:
                # Save Players using bulk upsert (same pattern as events)
                # Sort by ID to ensure consistent lock ordering and prevent deadlocks
                if player_objects:
                    players_data = [p.model_dump() for p in player_objects.values()]
                    players_data.sort(key=lambda p: p["id"])
                    stmt = pg_insert(Player).values(players_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["id"],
                        set_={
                            "name": stmt.excluded.name,
                            "position": stmt.excluded.position,
                        },
                    )
                    await session.exec(stmt)
                    await session.commit()

                # Save Events using Upsert (ON CONFLICT DO UPDATE) for Idempotency
                if event_objects:
                    # Convert SQLModel objects to dicts for bulk insert
                    events_data = [e.model_dump() for e in event_objects]

                    # Process in batches to avoid "too many arguments" error
                    batch_size = 500
                    for i in range(0, len(events_data), batch_size):
                        batch = events_data[i : i + batch_size]
                        stmt = pg_insert(Event).values(batch)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["id"], set_=stmt.excluded
                        )
                        await session.exec(stmt)

                    await session.commit()

            # Mark match as ingested (after successful completion)
            async with AsyncSession(engine) as session:
                await session.exec(
                    update(Match)
                    .where(col(Match.id) == match_id)
                    .values(events_ingested_at=datetime.utcnow())
                )
                await session.commit()

            logger.info(f"Marked match {match_id} as ingested")

        except Exception as e:
            logger.error(f"Error ingesting events: {e}")
            raise e
