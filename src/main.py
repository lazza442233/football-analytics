import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.api.routers import players, matches
from src.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise e
    yield


app = FastAPI(title="Football Analytics", lifespan=lifespan)

app.include_router(players.router)
app.include_router(matches.router)


@app.get("/health")
def health():
    return {"status": "ok"}
