import datetime
import uuid
from typing import cast

import pandas as pd
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.analytics.doppelganger import etl, schemas, service
from src.models import Competition, Event, Match, Player

# --- ETL Unit Tests ---


def test_minutes_estimation_empty():
    df = pd.DataFrame()
    minutes = etl.estimate_minutes_played(df)
    assert minutes.empty


def test_minutes_estimation_logic():
    # Setup mock event dataframe
    # Player 1: Matches 1 (full game), Match 2 (subbed on late)
    data = [
        # Match 1: min 1 to 90
        {"season_id": 2023, "match_id": 100, "player_id": 1, "minute": 1},
        {"season_id": 2023, "match_id": 100, "player_id": 1, "minute": 90},
        # Match 2: min 80 to 88 (subbed on) -> diff 8 -> +5 buffer -> 13
        {"season_id": 2023, "match_id": 101, "player_id": 1, "minute": 80},
        {"season_id": 2023, "match_id": 101, "player_id": 1, "minute": 88},
    ]
    df = pd.DataFrame(data)

    minutes_series = etl.estimate_minutes_played(df)

    # Check results
    # Match 1: 1 -> 90. Heuristic 1<5 and 90>85 => 90.0
    # Match 2: 80 -> 88. Diff 8. +5 = 13.0.
    # Total = 103.0

    assert minutes_series.loc[(2023, 1)] == 103.0


def test_assign_position_group():
    df = pd.DataFrame(
        [
            {"id": 1, "position": "Goalkeeper"},
            {"id": 2, "position": "Right Wing"},
            {"id": 3, "position": "Unknown Position"},
        ]
    )

    mapping = etl.assign_position_group(df)
    assert mapping.loc[0] == "GK"
    assert mapping.loc[1] == "FWD"
    assert mapping.loc[2] == "UNKNOWN"


def test_aggregate_stats_logic():
    # Mock aggregated events
    data = []
    # Create enough matches to pass 300 minutes threshold
    # 4 matches of 90 mins = 360 mins
    for i in range(4):
        # Match i
        match_id = 100 + i
        events = [
            {
                "season_id": 2023,
                "player_id": 1,
                "match_id": match_id,
                "minute": 1,
                "type": "Pass",
                "attributes": {},
                "location_x": 50,
                "location_y": 50,
            },
            {
                "season_id": 2023,
                "player_id": 1,
                "match_id": match_id,
                "minute": 90,
                "type": "Pass",
                "attributes": {"outcome": "Incomplete"},
                "location_x": 60,
                "location_y": 50,
            },
        ]
        if i == 0:
            # Add Shot in first match
            events.append(
                {
                    "season_id": 2023,
                    "player_id": 1,
                    "match_id": match_id,
                    "minute": 20,
                    "type": "Shot",
                    "attributes": {"xg": 0.5},
                    "location_x": 110,
                    "location_y": 40,
                }
            )
        data.extend(events)

    df = pd.DataFrame(data)

    stats = etl.aggregate_player_season_stats(df)

    row = cast(pd.Series, stats.loc[(2023, 1)])
    assert row["minutes_played"] == 360.0
    assert row["passes_attempted"] == 8
    assert row["shots_total"] == 1
    assert row["xg_total"] == 0.5

    # Normalized
    # 8 passes / 360 mins * 90 = 2.0
    assert row["passes_attempted_p90"] == 2.0


# --- Integration Tests (Service + Repo) ---


@pytest.fixture
async def doppelganger_data(session: AsyncSession):
    # Setup DB
    comp = Competition(id=99, name="Dpl League", gender="male")
    session.add(comp)

    match = Match(
        id=999,
        competition_id=99,
        season_id=2023,
        match_date=datetime.date(2023, 1, 1),
        home_team="H",
        away_team="A",
        home_score=0,
        away_score=0,
    )
    session.add(match)

    p1 = Player(id=10, name="Target Man", position="Center Forward")
    p2 = Player(id=20, name="Similar Guy", position="Right Wing")
    session.add(p1)
    session.add(p2)

    # Create 4 matches to satisfy > 300 minutes threshold
    matches = []
    for m_id in range(1001, 1005):  # 4 matches
        m = Match(
            id=m_id,
            competition_id=99,
            season_id=2023,
            match_date=datetime.date(2023, 1, 1),
            home_team="H",
            away_team="A",
            home_score=0,
            away_score=0,
        )
        session.add(m)
        matches.append(m)

    await session.commit()

    # Events for P1 and P2 in all 4 matches (full 90 mins each)
    events = []
    for m in matches:
        # P1
        events.append(
            Event(
                id=uuid.uuid4(),
                match_id=m.id,
                minute=1,
                second=0,
                type="Pass",
                player_id=10,
                team_id=1,
                location_x=50,
                location_y=50,
            )
        )
        events.append(
            Event(
                id=uuid.uuid4(),
                match_id=m.id,
                minute=90,
                second=0,
                type="Pass",
                player_id=10,
                team_id=1,
                location_x=60,
                location_y=50,
            )
        )
        # P2
        events.append(
            Event(
                id=uuid.uuid4(),
                match_id=m.id,
                minute=1,
                second=0,
                type="Pass",
                player_id=20,
                team_id=1,
                location_x=50,
                location_y=50,
            )
        )
        events.append(
            Event(
                id=uuid.uuid4(),
                match_id=m.id,
                minute=90,
                second=0,
                type="Shot",
                player_id=20,
                team_id=1,
                location_x=100,
                location_y=40,
                attributes={"xg": 0.1},
            )
        )

    for e in events:
        session.add(e)

    await session.commit()
    return True


@pytest.mark.asyncio
async def test_build_season_dataset(session: AsyncSession, doppelganger_data):
    svc = service.DoppelgangerService(session)
    df = await svc.build_season_dataset(season_id=2023)

    assert not df.empty
    # We have 2 players
    assert len(df) == 2

    # Check Index
    assert (2023, 10) in df.index
    assert (2023, 20) in df.index

    # Check Position Groups
    # P1 (CF) -> FWD
    # P2 (RW) -> FWD
    p1_stats = cast(pd.Series, df.loc[(2023, 10)])
    p2_stats = cast(pd.Series, df.loc[(2023, 20)])

    assert p1_stats["position_group"] == "FWD"
    assert p2_stats["position_group"] == "FWD"

    # Check Mins
    # 4 matches * 90 = 360
    assert p1_stats["minutes_played"] == 360.0
    assert p2_stats["minutes_played"] == 360.0


@pytest.mark.asyncio
async def test_get_player_stats(session: AsyncSession, doppelganger_data):
    svc = service.DoppelgangerService(session)

    # Get P1 stats
    stats = await svc.get_player_stats(player_id=10, season_id=2023)

    assert stats is not None
    assert stats["minutes_played"] == 360.0

    # Non existent player
    missing = await svc.get_player_stats(player_id=9999, season_id=2023)
    assert missing is None


def test_schemas():
    # Quick coverage for schemas logic
    q = schemas.DoppelgangerQuery(player_id=1, season_id=2023, limit=10)
    assert q.limit == 10

    # Boundary check
    q2 = schemas.DoppelgangerQuery(player_id=1, season_id=2023, limit=20)
    assert q2.limit == 20
