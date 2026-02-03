import asyncio
import logging
import os
import sys

from sqlmodel import SQLModel

from src.database import engine
from src.services.ingestion import StatsBombIngestionService

# Add project root to path so src is importable
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_ingestion():
    logger.info("Starting Data Ingestion...")

    # 0. Ensure Database Tables Exist
    logger.info("Ensuring database tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 1. Ingestion
    # Target: UEFA Euro 2024 (ID 55, Season 282)

    # You can uncomment other competitions if needed
    targets = [
        (55, 282, "UEFA Euro 2024"),
        # (9, 281, "Bundesliga 2023/2024")
    ]

    ingest_service = StatsBombIngestionService()

    for comp_id, season_id, name in targets:
        logger.info(f"--- Ingesting {name} ---")
        try:
            await ingest_service.ingest_season_matches(
                comp_id, season_id, ingest_events=True
            )
            logger.info(f"Successfully ingested {name}")
        except Exception as e:
            logger.error(f"Ingestion failed for {name}: {e}")

    logger.info("Ingestion Complete.")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
