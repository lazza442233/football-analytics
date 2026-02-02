import asyncio
import logging
from src.services.ingestion import StatsBombIngestionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Using 2022 World Cup as the target to satisfy the "Argentina" verification
    # Competition ID 43 = FIFA World Cup
    # Season ID 106 = 2022
    service = StatsBombIngestionService()
    asyncio.run(service.ingest_season_matches(
        competition_id=43, season_id=106))
