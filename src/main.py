from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database import engine, get_session
from src.models import Player
import logging

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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/players", response_model=Player)
async def create_player(player: Player, session: AsyncSession = Depends(get_session)):
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player
