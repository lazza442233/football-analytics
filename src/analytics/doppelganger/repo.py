from typing import List

import pandas as pd
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Event, Match, Player


async def fetch_season_events(session: AsyncSession, season_id: int) -> pd.DataFrame:
    """
    Fetches all events for a specific season into a Pandas DataFrame.
    optimized for analytical workload.
    """
    # We construct a query to select relevant fields
    # Joining Match to filter by season_id
    query = (
        select(
            Event.id,
            Event.match_id,
            Event.player_id,
            Event.type,
            Event.minute,
            Event.location_x,
            Event.location_y,
            Event.attributes,
            Match.season_id,  # type: ignore
            Match.home_team,  # type: ignore
            Match.away_team,  # type: ignore
        )
        .join(Match, Event.match_id == Match.id)
        .where(Match.season_id == season_id)
        .where(Event.player_id.is_not(None))  # type: ignore
    )

    # Execute asynchronously
    result = await session.exec(query)
    data = result.all()

    if not data:
        return pd.DataFrame()

    # Convert to DataFrame
    # SQLAlchemy Row objects keys are derived from column names
    df = pd.DataFrame(data)

    # Ensure correct column names (sometimes they might be ambiguous in joins)
    # The order matches the select list
    expected_cols = [
        "id",
        "match_id",
        "player_id",
        "type",
        "minute",
        "location_x",
        "location_y",
        "attributes",
        "season_id",
        "home_team",
        "away_team",
    ]
    df.columns = expected_cols

    return df


async def fetch_player_season_events(
    session: AsyncSession, season_id: int, player_id: int
) -> pd.DataFrame:
    """
    Fetches events for a single player in a season.
    Optimized for single-target analysis.
    """
    query = (
        select(
            Event.id,
            Event.match_id,
            Event.player_id,
            Event.type,
            Event.minute,
            Event.location_x,
            Event.location_y,
            Event.attributes,
            Match.season_id,  # type: ignore
            Match.home_team,  # type: ignore
            Match.away_team,  # type: ignore
        )
        .join(Match, Event.match_id == Match.id)
        .where(Match.season_id == season_id)
        .where(Event.player_id == player_id)
    )

    result = await session.exec(query)
    data = result.all()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    expected_cols = [
        "id",
        "match_id",
        "player_id",
        "type",
        "minute",
        "location_x",
        "location_y",
        "attributes",
        "season_id",
        "home_team",
        "away_team",
    ]
    df.columns = expected_cols
    return df


async def fetch_player_metadata(
    session: AsyncSession, player_ids: List[int]
) -> pd.DataFrame:
    """
    Fetches player names and positions for enriching the results.
    """
    query = select(Player.id, Player.name, Player.position).where(
        Player.id.in_(player_ids)  # type: ignore
    )
    result = await session.exec(query)
    data = result.all()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df.columns = ["id", "name", "position"]
    return df
