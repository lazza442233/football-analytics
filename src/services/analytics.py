from typing import Dict

from sqlmodel import Float, cast, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Event


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

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
