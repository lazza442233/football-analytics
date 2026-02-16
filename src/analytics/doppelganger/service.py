from typing import Any, Dict, Optional

import pandas as pd
from sqlmodel.ext.asyncio.session import AsyncSession

from src.analytics.doppelganger import etl, explain, preprocess, repo, schemas
from src.analytics.doppelganger.config import MIN_MINUTES, SIMILARITY_FLOOR
from src.analytics.doppelganger.errors import (
    InsufficientDataError,
    InvalidPositionError,
    NoMatchesError,
    PlayerSeasonNotFoundError,
)
from src.analytics.doppelganger.registry import registry
from src.analytics.doppelganger.types import PositionGroup


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
        """
        # Extraction (Events)
        events_df = await repo.fetch_season_events(self.session, season_id)

        if events_df.empty:
            return pd.DataFrame()

        # Extraction (Metadata)
        unique_player_ids = events_df["player_id"].unique().tolist()
        player_meta_df = await repo.fetch_player_metadata(
            self.session, unique_player_ids
        )

        # Transformation
        stats_df = etl.aggregate_player_season_stats(events_df)

        if stats_df.empty:
            return pd.DataFrame()

        # Enrich with Position Groups
        player_meta_df = player_meta_df.set_index("id")
        position_map = etl.assign_position_group(player_meta_df)

        # Reset index to make join easy, or map directly
        stats_df = stats_df.reset_index()
        stats_df["position_group"] = (
            stats_df["player_id"].map(position_map).fillna("UNKNOWN")
        )
        stats_df["name"] = (
            stats_df["player_id"].map(player_meta_df["name"]).fillna("Unknown")
        )

        stats_df = stats_df.set_index(["season_id", "player_id"])

        return stats_df

    async def train_season_models(self, season_id: int) -> Dict[str, int]:
        """
        Builds the dataset for a season and trains models for all position groups.
        Populates the global in-memory registry.
        """
        from src.analytics.doppelganger import train

        # 1. Build Dataset
        df_season = await self.build_season_dataset(season_id)

        if df_season.empty:
            return {}

        results = {}

        # 2. Split by Position Group
        # Iterate over known groups to ensure we cover all of them
        for group in PositionGroup:
            group_val = group.value

            # Filter for this group
            df_group = df_season[df_season["position_group"] == group_val]

            if df_group.empty:
                continue

            # 3. Train
            bundle = train.train_model_for_group(df_group, group_val)

            # 4. Register
            registry.register(group_val, bundle)
            results[group_val] = bundle.vector_count

        return results

    async def get_player_stats(
        self, player_id: int, season_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the 'DNA' for a specific player-season.
        """
        events_df = await repo.fetch_player_season_events(
            self.session, season_id, player_id
        )

        if events_df.empty:
            return None

        player_meta_df = await repo.fetch_player_metadata(self.session, [player_id])

        stats_df = etl.aggregate_player_season_stats(events_df)

        if stats_df.empty:
            return None

        # Enrich
        player_meta_df = player_meta_df.set_index("id")
        position_map = etl.assign_position_group(player_meta_df)
        stats_df = stats_df.reset_index()
        stats_df["position_group"] = (
            stats_df["player_id"].map(position_map).fillna("UNKNOWN")
        )
        stats_df = stats_df.set_index(["season_id", "player_id"])

        # Locate player
        try:
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
        """
        # 1. Get target player stats (their "DNA")
        player_stats = await self.get_player_stats(query.player_id, query.season_id)

        if not player_stats:
            raise PlayerSeasonNotFoundError(query.player_id, query.season_id)

        # 2. Extract position group and validate minutes
        position_group = query.position_group or player_stats.get(
            "position_group", "UNKNOWN"
        )

        # Validate Position
        valid_positions = {p.value for p in PositionGroup}
        if position_group not in valid_positions:
            raise InvalidPositionError(query.player_id, str(position_group))

        minutes_played = player_stats.get("minutes_played", 0.0)

        if minutes_played < MIN_MINUTES:
            raise InsufficientDataError(
                query.player_id, int(minutes_played), MIN_MINUTES
            )

        # 3. Load the trained model bundle for this position group
        bundle = registry.get(position_group)

        if not bundle:
            # No model trained for this position group
            return schemas.DoppelgangerResponse(
                meta=schemas.DoppelgangerMeta(
                    model_version=pd.Timestamp.now(),
                    position_group=position_group,
                    vector_count=0,
                ),
                target=schemas.TargetPlayer(
                    name="Unknown",
                    season_id=query.season_id,
                    position=position_group,  # type: ignore
                ),
                similar_players=[],
            )

        # 4. Build feature frame for target player
        # Convert dict to DataFrame row
        target_df = pd.DataFrame([player_stats])
        target_features = preprocess.build_feature_frame(target_df)

        if target_features.empty:
            raise InsufficientDataError(
                query.player_id, int(minutes_played), MIN_MINUTES
            )

        # 5. Scale the target player's features
        target_scaled = bundle.scaler.transform(target_features)

        # 6. Find k nearest neighbors
        # Request k+1 to account for the target player potentially being in the dataset
        k = min(query.limit + 1, bundle.vector_count)
        distances, indices = bundle.knn.kneighbors(target_scaled, n_neighbors=k)

        # Flatten arrays (since we only have one query point)
        distances = distances[0]
        indices = indices[0]

        # 7. Get the fitted vectors from the knn model for generating explanations
        # The NearestNeighbors model stores the fitted data in _fit_X
        fitted_vectors = bundle.knn._fit_X  # type: ignore

        # 8. Filter out the target player if they appear in results
        # and apply similarity threshold
        similar_players: list[schemas.SimilarPlayerResult] = []

        for idx, distance in zip(indices, distances):
            entity = bundle.entities[idx]

            # Skip if this is the target player themselves
            if (
                entity.player_id == query.player_id
                and entity.season_id == query.season_id
            ):
                continue

            # Convert distance to similarity score
            # For cosine metric: similarity = 1 - distance
            similarity_score = 1.0 - distance

            # Apply similarity threshold
            if similarity_score < SIMILARITY_FLOOR:
                continue

            # Get the pre-computed scaled vector for this match
            match_scaled = fitted_vectors[idx]

            # Generate explanation
            explanation_dict = explain.explain_match(
                target_scaled[0], match_scaled, bundle.feature_names
            )

            similar_players.append(
                schemas.SimilarPlayerResult(
                    player_id=entity.player_id,
                    name=entity.name,
                    season_id=entity.season_id,
                    similarity_score=round(similarity_score, 3),
                    explanation=schemas.SimilarPlayerExplanation(
                        # type: ignore
                        shared_strengths=explanation_dict["shared_strengths"],
                        key_difference=explanation_dict.get("key_difference"),  # type: ignore
                    ),
                )
            )

            # Stop once we have enough results
            if len(similar_players) >= query.limit:
                break

        # 9. Handle case where no matches found
        if not similar_players:
            raise NoMatchesError(SIMILARITY_FLOOR)

        # 10. Build and return response
        # Try to get target player name from metadata
        target_name = "Unknown"
        player_meta = await repo.fetch_player_metadata(self.session, [query.player_id])
        if not player_meta.empty:
            target_name = player_meta.iloc[0]["name"]

        return schemas.DoppelgangerResponse(
            meta=schemas.DoppelgangerMeta(
                model_version=bundle.timestamp,
                position_group=position_group,
                vector_count=bundle.vector_count,
            ),
            target=schemas.TargetPlayer(
                name=target_name,
                season_id=query.season_id,
                position=position_group,  # type: ignore
            ),
            similar_players=similar_players,
        )
