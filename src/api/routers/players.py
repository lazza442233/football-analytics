from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.models import Player
from src.services.analytics import AnalyticsService

router = APIRouter(prefix="/players", tags=["Players"])


class PlayerSeasonStats(BaseModel):
    player_id: int
    season_id: int
    matches_played: int
    total_passes: int
    successful_passes: int
    pass_completion_rate: float
    total_xg: float


@router.post("", response_model=Player)
async def create_player(player: Player, session: AsyncSession = Depends(get_session)):
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@router.get("/{player_id}/stats/season/{season_id}", response_model=PlayerSeasonStats)
async def get_player_season_stats(
    player_id: int, season_id: int, session: AsyncSession = Depends(get_session)
):
    service = AnalyticsService(session)
    stats = await service.get_player_season_stats(player_id, season_id)
    if not stats:
        raise HTTPException(
            status_code=404, detail="Stats not found for player in this season")
    return stats
