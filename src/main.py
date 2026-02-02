import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from sqlalchemy import text

from src.api.routers import analytics, ingest, matches, players
from src.config import settings
from src.database import engine
from src.logging_conf import configure_logging

# Configure logging before creating the app
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database connection setup
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise e

    # Redis/ARQ connection setup
    try:
        app.state.arq_pool = await create_pool(
            RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        )
        logger.info("Connected to Redis/ARQ")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")

    yield

    # Cleanup
    if hasattr(app.state, "arq_pool"):
        await app.state.arq_pool.close()


app = FastAPI(title="Football Analytics", lifespan=lifespan)

app.include_router(players.router)
app.include_router(matches.router)
app.include_router(analytics.router)
app.include_router(ingest.router)


@app.get("/health")
def health():
    return {"status": "ok"}
