
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.models import Match
from src.services.analytics import AnalyticsService

router = APIRouter(prefix="/matches", tags=["Analytics"])


class MatchXGSummary(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    home_xg: float
    away_xg: float


@router.get("/{match_id}/analytics/summary", response_model=MatchXGSummary)
async def get_match_xg_summary(
    match_id: int,
    session: AsyncSession = Depends(get_session)
):
    match_stmt = select(Match).where(Match.id == match_id)
    match_result = await session.exec(match_stmt)
    match = match_result.first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    analytics_service = AnalyticsService(session)
    xg_map = await analytics_service.get_xg_by_team(match_id)

    return MatchXGSummary(
        match_id=match_id,
        home_team=match.home_team,
        away_team=match.away_team,
        home_xg=round(xg_map.get(match.home_team, 0.0), 2),
        away_xg=round(xg_map.get(match.away_team, 0.0), 2)
    )
