# Ensure models are imported for metadata creation
import asyncio
import logging

# Add project root to path so src is importable
import os
import sys

import pandas as pd
from sqlmodel import SQLModel

from src.analytics.doppelganger import etl, registry, repo, train
from src.database import engine
from src.models import Player
from src.services.ingestion import StatsBombIngestionService

sys.path.append(os.getcwd())


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_end_to_end_test():
    logger.info("Starting End-to-End Test for Doppelgänger Engine")

    # 0. Ensure Database Tables Exist
    logger.info("Ensuring database tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 1. Ingestion
    # Target: UEFA Euro 2024 (ID 55, Season 282)
    # Target: Bundesliga 2023/2024 (ID 9, Season 281)

    targets = [
        (55, 282, "UEFA Euro 2024"),
        # (9, 281, "Bundesliga 2023/2024")
    ]

    ingest_service = StatsBombIngestionService()

    for comp_id, season_id, name in targets:
        logger.info(f"--- Ingesting {name} ---")
        # ingest_events=True is critical
        try:
            await ingest_service.ingest_season_matches(
                comp_id, season_id, ingest_events=True
            )
        except Exception as e:
            logger.error(f"Ingestion failed for {name}: {e}")
            # Continue to next or fail? Let's try to continue if one works.

    # 2. ETL & Training
    logger.info("--- Starting Doppelgänger Setup ---")

    async with engine.connect() as conn:
        # We need a session mainly for etl.repo which expects an AsyncSession
        pass

    # We need to use a session context for repo calls
    from sqlmodel.ext.asyncio.session import AsyncSession

    async with AsyncSession(engine) as session:
        # We process each competition we ingested
        all_stats = []

        for comp_id, season_id, name in targets:
            logger.info(f"Fetching events for {name} for ETL...")
            events_df = await repo.fetch_season_events(session, season_id)

            if events_df.empty:
                logger.warning(f"No events found for {name}. Skipping.")
                continue

            logger.info(
                f"Calculating aggregated stats for {name} ({len(events_df)} events)..."
            )

            # Need to ensure we fetch player metadata (position)
            # In current repo implementation, we might need a separate fetch for players
            # or join etl.assign_position_group requires 'position' column/info.

            # repo.fetch_season_events returns: id, match_id, player_id, type...
            # It does NOT return player position.

            # We need to fetch player metadata.
            # Currently repo.py doesn't have fetch_players_metadata(season_id).
            # We can quickly add a query here or use raw sql.

            # Let's inspect events_df columns
            logger.info(f"Events Columns: {events_df.columns}")

            # Run aggregation
            stats_df = etl.aggregate_player_season_stats(events_df)

            if stats_df.empty:
                logger.warning(f"No aggregated stats for {name}.")
                continue

            # Now we need Position info.
            # Ingest saved Player models with positions.
            # Let's fetch all players involved in this season.
            from sqlmodel import select

            unique_player_ids = (
                stats_df.index.get_level_values("player_id").unique().tolist()
            )

            if not unique_player_ids:
                continue

            q = select(Player).where(Player.id.in_(unique_player_ids))
            player_results = await session.exec(q)
            players = player_results.all()

            player_meta = pd.DataFrame([p.model_dump() for p in players])
            if player_meta.empty:
                logger.warning("No player metadata found.")
                continue

            # player_meta should have 'id' and 'position'.
            # stats_df index is (season_id, player_id).

            # Join stats with player metadata
            stats_df = stats_df.reset_index()
            stats_df = stats_df.merge(
                player_meta[["id", "position", "name"]],
                left_on="player_id",
                right_on="id",
                how="left",
            )

            # Assign groups
            stats_df["position_group"] = etl.assign_position_group(stats_df)

            # Drop invalid groups
            stats_df = stats_df[stats_df["position_group"] != "UNKNOWN"]

            all_stats.append(stats_df)

    if not all_stats:
        logger.error("No stats available for training.")
        return

    full_df = pd.concat(all_stats, ignore_index=True)

    # 3. Training & Registry
    logger.info("--- Training Models ---")

    groups = full_df["position_group"].unique()
    for group in groups:
        logger.info(f"Training for group: {group}...")
        group_df = full_df[full_df["position_group"] == group].copy()

        # Set index back to season_id, player_id for train function expectations?
        # train_model_for_group docstring says:
        # "Index is expected to be (season_id, player_id) or just range index provided
        # columns specific to that are present."
        # It resets index internally anyway to iterate.

        bundle = train.train_model_for_group(group_df, group)
        registry.registry.register(group, bundle)

    logger.info("--- Registry Status ---")
    logger.info(registry.registry.status)

    # 4. Verification Check
    # Pick a random player from the registry and find neighbors
    logger.info("--- Verification: Find Neighbors ---")

    # Let's try to find a known player in the registry bundles
    found = False
    for group, bundle in registry.registry._bundles.items():
        if found:
            break
        for i, vec in enumerate(bundle.entities):
            # Just pick the first one
            # Access the underlying matrix stored in the sklearn object
            target_vec = bundle.knn._fit_X[i]
            neighbors = bundle.knn.kneighbors(
                [target_vec],
                n_neighbors=min(5, len(bundle.entities)),
                return_distance=True,
            )

            logger.info(f"Query Player: {vec.player_id} ({group})")
            indices = neighbors[1][0]
            distances = neighbors[0][0]

            for idx, dist in zip(indices, distances):
                neighbor_meta = bundle.entities[idx]
                logger.info(
                    f"   -> Neighbor: {neighbor_meta.player_id} (Dist: {dist:.4f})"
                )

            found = True
            break

    logger.info("End-to-End Test Complete.")


if __name__ == "__main__":
    asyncio.run(run_end_to_end_test())
