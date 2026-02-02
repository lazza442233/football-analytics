from typing import Dict, List, Optional

from sqlmodel import Float, cast, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Event


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_events(
        self,
        match_id: int,
        event_type: Optional[str] = None,
        player_id: Optional[int] = None,
        min_minute: Optional[int] = None,
        max_minute: Optional[int] = None,
    ) -> List[Event]:
        """
        Dynamic search for events within a match.
        """
        stmt = select(Event).where(Event.match_id == match_id)

        if event_type:
            stmt = stmt.where(Event.type == event_type)

        if player_id:
            stmt = stmt.where(Event.player_id == player_id)

        if min_minute is not None:
            stmt = stmt.where(Event.minute >= min_minute)

        if max_minute is not None:
            stmt = stmt.where(Event.minute <= max_minute)

        # Order by minute, second
        stmt = stmt.order_by(Event.minute, Event.second)  # type: ignore

        result = await self.session.exec(stmt)
        return result.all()  # type: ignore

    async def get_xg_by_team(self, match_id: int) -> Dict[str, float]:
        """
        Calculates the total Expected Goals (xG) for each team in a match.
        Returns a dictionary: {"Team A": 1.25, "Team B": 0.88}
        """
        # CAST(attributes->>'shot_statsbomb_xg' as Float)
        xg_expr = cast(Event.attributes["shot_statsbomb_xg"].astext, Float)
        team_name_expr = Event.attributes["team"].astext

        stmt = (
            select(team_name_expr, func.sum(xg_expr))
            .where(Event.match_id == match_id)
            .where(Event.type == "Shot")
            .group_by(team_name_expr)
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        # Transform Row('TeamName', 1.23) -> {'TeamName': 1.23}
        return {row[0]: (row[1] or 0.0) for row in rows}
