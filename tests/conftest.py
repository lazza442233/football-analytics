import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.main import app
from src.database import get_session
# Ensure your config uses the env var DATABASE_URL
from src.config import settings

# Override the engine to use the TEST database URL
# Prioritize env var (for CI) over computed settings
DB_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
test_engine = create_async_engine(DB_URL, echo=False)


@pytest.fixture(name="session")
async def session_fixture():
    # 1. Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 2. Return session
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    # 3. Cleanup (Drop tables)
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession):
    # Override the get_session dependency in the app
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    # Return the TestClient (Async version)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
