import logging
from typing import Any

from arq.connections import RedisSettings

from src.config import settings
from src.database import engine
from src.logging_conf import configure_logging
from src.services.ingestion import StatsBombIngestionService

configure_logging()
logger = logging.getLogger(__name__)


async def startup(ctx: Any):
    logger.info("Worker starting up...")
    # Add any startup logic here, e.g. checking DB connection
    # Note: StatsBombIngestionService manages its own DB sessions/engine usage mostly,
    # but uses src.database.engine global.


async def shutdown(ctx: Any):
    logger.info("Worker shutting down...")
    await engine.dispose()


async def ingest_season_task(
    ctx: Any, competition_id: int, season_id: int, ingest_events: bool = True
):
    """
    Background job to ingest matches and events for a competition/season.
    """
    logger.info(
        f"Starting ingestion job for Comp: {competition_id}, "
        f"Season: {season_id}, Events: {ingest_events}"
    )

    service = StatsBombIngestionService()
    await service.ingest_season_matches(
        competition_id=competition_id,
        season_id=season_id,
        ingest_events=ingest_events,
    )
    logger.info(
        f"Finished ingestion job for Comp: {competition_id}, Season: {season_id}"
    )


class WorkerSettings:
    functions = [ingest_season_task]
    redis_settings = RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 1
