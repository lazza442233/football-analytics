import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import text

from src.analytics.doppelganger.service import DoppelgangerService
from src.api.routers import analytics, doppelganger, ingest, matches, players
from src.config import settings
from src.database import engine, get_session
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

    # Dev Helper: Auto-train Doppelgänger models for commonly used seasons
    # if in development. This prevents the "vector_count: 0" issue on reload
    try:
        seasons_to_train = [282, 106]  # 282: EPL 03/04, 106: World Cup 2022
        async for session in get_session():
            svc = DoppelgangerService(session)
            for season_id in seasons_to_train:
                logger.info(
                    f"Auto-training Doppelgänger models for Season {season_id}..."
                )
                try:
                    counts = await svc.train_season_models(season_id)
                    logger.info(f"Season {season_id} Training Complete: {counts}")
                except Exception as ex:
                    # Don't crash startup if one season fails (e.g. data missing)
                    logger.warning(f"Could not train season {season_id}: {ex}")
            break
    except Exception as e:
        logger.warning(f"Auto-training loop failed: {e}")

    yield

    # Cleanup
    if hasattr(app.state, "arq_pool"):
        await app.state.arq_pool.close()


app = FastAPI(
    title="Football Analytics",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(players.router)
app.include_router(matches.router)
app.include_router(analytics.router)
app.include_router(doppelganger.router)
app.include_router(ingest.router)


@app.get("/health")
def health():
    return {"status": "ok"}
