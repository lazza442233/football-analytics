from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database import get_session
from src.models import Player

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("", response_model=Player)
async def create_player(player: Player, session: AsyncSession = Depends(get_session)):
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player
