from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.analytics.doppelganger.service import DoppelgangerService
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
    # New Field: The normalized per-90 metrics (DNA)
    advanced_metrics: Dict[str, Any] = {}


@router.get("/search", response_model=List[Player])
async def search_players(name: str, session: AsyncSession = Depends(get_session)):
    """
    Search players by name (case-insensitive partial match).
    """
    if not name:
        return []

    # Use unaccent() to handle "mbappe" matching "Mbappé"
    # Requires: CREATE EXTENSION IF NOT EXISTS unaccent;
    statement = (
        select(Player)
        .where(func.unaccent(Player.name).ilike(func.unaccent(f"%{name}%")))
        .limit(10)
    )
    result = await session.exec(statement)
    return result.all()


@router.post("", response_model=Player)
async def create_player(player: Player, session: AsyncSession = Depends(get_session)):
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@router.get("/{player_id}/seasons", response_model=List[int])
async def get_player_seasons(
    player_id: int, session: AsyncSession = Depends(get_session)
):
    analytics_service = AnalyticsService(session)
    seasons = await analytics_service.get_player_seasons(player_id)
    return seasons


@router.get("/{player_id}/stats/season/{season_id}", response_model=PlayerSeasonStats)
async def get_player_season_stats(
    player_id: int, season_id: int, session: AsyncSession = Depends(get_session)
):
    # Original Service for Aggregate Counts
    analytics_service = AnalyticsService(session)
    count_stats = await analytics_service.get_player_season_stats(player_id, season_id)

    if not count_stats:
        raise HTTPException(
            status_code=404, detail="Stats not found for player in this season"
        )

    # Doppelgänger Service for Advanced "DNA" Metrics (Per 90s)
    doppel_service = DoppelgangerService(session)
    dna_stats = await doppel_service.get_player_stats(player_id, season_id) or {}

    # Merge the results
    return PlayerSeasonStats(**count_stats, advanced_metrics=dna_stats)
