from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from src.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check DB connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ SUCCESS: Connected to Docker PostgreSQL Database!")
    except Exception as e:
        logger.error(f"❌ FAILURE: Database connection failed: {e}")
        raise e
    yield
    # Shutdown logic (if any)

app = FastAPI(title="Football Analytics", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
