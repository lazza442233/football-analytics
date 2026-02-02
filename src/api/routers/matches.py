from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.models import Event

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/{match_id}/events", response_model=List[Event])
async def get_match_events(
    match_id: int,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Event).where(Event.match_id == match_id)
    result = await session.exec(stmt)
    return result.all()
