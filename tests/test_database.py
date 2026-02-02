import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Player


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
