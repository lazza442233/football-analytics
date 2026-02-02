from typing import Any, Dict, Optional

import pandas as pd
from sqlmodel.ext.asyncio.session import AsyncSession

from src.analytics.doppelganger import etl, repo, schemas


class DoppelgangerService:
    """
    Orchestrates the Doppelgänger Engine pipeline.
    Phase 1: ETL & Aggregation.
    Phase 2: Vectorization & Inference.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def build_season_dataset(self, season_id: int) -> pd.DataFrame:
        """
        End-to-end pipeline to build the 'DNA' dataset for a specific season.
        1. Fetch raw events.
        2. Fetch player metadata (positions).
        3. Aggregate, Normalize & Enrich.
        """
        # 1. Extraction (Events)
        events_df = await repo.fetch_season_events(self.session, season_id)

        if events_df.empty:
            return pd.DataFrame()

        # 2. Extraction (Metadata)
        unique_player_ids = events_df["player_id"].unique().tolist()
        player_meta_df = await repo.fetch_player_metadata(
            self.session, unique_player_ids
        )

        # 3. Transformation
        stats_df = etl.aggregate_player_season_stats(events_df)

        if stats_df.empty:
            return pd.DataFrame()

        # 4. Enrich with Position Groups
        # stats_df index is (season_id, player_id)
        # We need to join on player_id level
        position_map = etl.assign_position_group(player_meta_df)

        # Reset index to make join easy, or map directly
        stats_df = stats_df.reset_index()
        stats_df["position_group"] = (
            stats_df["player_id"].map(position_map).fillna("UNKNOWN")
        )

        # Set index back to (season_id, player_id)
        stats_df = stats_df.set_index(["season_id", "player_id"])

        return stats_df

    async def get_player_stats(
        self, player_id: int, season_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the 'DNA' for a specific player-season.
        """
        # Optimized: Fetch only this player's events
        events_df = await repo.fetch_player_season_events(
            self.session, season_id, player_id
        )

        if events_df.empty:
            return None

        # Fetch metadata for this single player
        player_meta_df = await repo.fetch_player_metadata(self.session, [player_id])

        stats_df = etl.aggregate_player_season_stats(events_df)

        if stats_df.empty:
            return None

        # Enrich
        position_map = etl.assign_position_group(player_meta_df)
        stats_df = stats_df.reset_index()
        stats_df["position_group"] = (
            stats_df["player_id"].map(position_map).fillna("UNKNOWN")
        )
        stats_df = stats_df.set_index(["season_id", "player_id"])

        # Locate player
        try:
            # Type cast for static analysis safety
            # Index is (season_id, player_id)
            player_series = stats_df.loc[(season_id, player_id)]

            if isinstance(player_series, pd.Series):
                return player_series.to_dict()  # type: ignore
            # Handle edge case where duplicate index might return DataFrame
            return player_series.iloc[0].to_dict()  # type: ignore
        except KeyError:
            return None

    async def search_similar_players(
        self, query: schemas.DoppelgangerQuery
    ) -> schemas.DoppelgangerResponse:
        """
        Phase 2: Use Vectorizer to find nearest neighbors.
        (Not yet implemented)
        """
        raise NotImplementedError("Phase 2: Vectorization Engine not yet implemented")
