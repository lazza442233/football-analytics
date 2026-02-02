import asyncio
import logging
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from statsbombpy import sb

from src.database import engine
from src.models import Competition, Match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ingest_matches(competition_id: int, season_id: int):
    logger.info(
        f"Starting ingestion for Competition={competition_id}, Season={season_id}")

    # 1. Ensure Competition exists (FK Constraint)
    # We fetch all competitions to find the metadata for the requested one
    comps_df = sb.competitions()

    # Filter for specific competition/season
    target_comp = comps_df[
        (comps_df['competition_id'] == competition_id) &
        (comps_df['season_id'] == season_id)
    ]

    if target_comp.empty:
        logger.error(
            f"Competition {competition_id} / Season {season_id} not found in StatsBomb.")
        return

    comp_row = target_comp.iloc[0]
    competition = Competition(
        id=int(comp_row['competition_id']),
        name=str(comp_row['competition_name']),
        gender=str(comp_row['competition_gender'])
    )

    async with AsyncSession(engine) as session:
        logger.info(f"Upserting Competition: {competition.name}")
        await session.merge(competition)
        await session.commit()

    # 2. Fetch Matches
    try:
        matches_df = sb.matches(
            competition_id=competition_id, season_id=season_id)
    except Exception as e:
        logger.error(f"Failed to fetch matches: {e}")
        return

    logger.info(f"Found {len(matches_df)} matches.")

    async with AsyncSession(engine) as session:
        for _, row in matches_df.iterrows():
            match = Match(
                id=int(row['match_id']),
                competition_id=competition_id,
                match_date=pd.to_datetime(row['match_date']).date(),
                home_team=str(row['home_team']),
                away_team=str(row['away_team']),
                home_score=int(row['home_score']),
                away_score=int(row['away_score'])
            )
            # Use merge for upsert (idempotent)
            await session.merge(match)

        await session.commit()
        logger.info("Matches upserted successfully.")


if __name__ == "__main__":
    # Using 2022 World Cup as the target to satisfy the "Argentina" verification
    # Competition ID 43 = FIFA World Cup
    # Season ID 106 = 2022
    asyncio.run(ingest_matches(competition_id=43, season_id=106))
