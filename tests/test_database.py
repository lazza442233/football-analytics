import pytest
import pytest_asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import settings
from src.models import Player

# In CI environments, we prefer the explicit DATABASE_URL env var if available.
# Locally, we fall back to the constructed settings from .env.
import os

DB_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
engine = create_async_engine(DB_URL, echo=True, future=True)


@pytest_asyncio.fixture
async def session():
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_player(session: AsyncSession):
    # Arange
    new_player = Player(name="Lionel Messi", position="Forward")

    # Act
    session.add(new_player)
    await session.commit()
    await session.refresh(new_player)

    # Assert
    assert new_player.id is not None
    assert new_player.name == "Lionel Messi"

    # Cleanup (Optional, but good for repeatability in this simple setup)
    # real tests would use transaction rollbacks or test DBs
    await session.delete(new_player)
    await session.commit()
