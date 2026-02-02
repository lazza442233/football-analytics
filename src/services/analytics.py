from typing import Any, Dict, List, Optional

from sqlmodel import Float, cast, col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Event, Match


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_player_season_stats(
        self, player_id: int, season_id: int
    ) -> Dict[str, Any]:
        """
        Aggregates stats for a player across a specific season.
        """
        # count(distinct match_id)
        # count(passes)
        # count(successful_passes) -> pass_outcome IS NULL
        # sum(xg) -> shot_statsbomb_xg

        stmt = (
            select(
                func.count(func.distinct(col(Match.id))),
                func.count(col(Event.id)).filter(col(Event.type) == "Pass"),
                func.count(col(Event.id)).filter(
                    (col(Event.type) == "Pass")
                    & (~func.jsonb_exists(col(Event.attributes), "pass_outcome"))
                ),
                func.sum(
                    cast(col(Event.attributes)["shot_statsbomb_xg"].astext, Float)
                ),
            )
            .join(Match, col(Match.id) == col(Event.match_id))
            .where(col(Event.player_id) == player_id)
            .where(col(Match.season_id) == season_id)
        )

        result = await self.session.exec(stmt)
        row = result.first()

        if not row:
            return {
                "player_id": player_id,
                "season_id": season_id,
                "matches_played": 0,
                "total_passes": 0,
                "successful_passes": 0,
                "pass_completion_rate": 0.0,
                "total_xg": 0.0,
            }

        matches_played, total_passes, successful_passes, total_xg = row

        matches_played = matches_played or 0
        total_passes = total_passes or 0
        successful_passes = successful_passes or 0
        total_xg = round(total_xg, 2) if total_xg else 0.0

        pass_completion_rate = 0.0
        if total_passes > 0:
            pass_completion_rate = round((successful_passes / total_passes) * 100, 2)

        return {
            "player_id": player_id,
            "season_id": season_id,
            "matches_played": matches_played,
            "total_passes": total_passes,
            "successful_passes": successful_passes,
            "pass_completion_rate": pass_completion_rate,
            "total_xg": total_xg,
        }

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
