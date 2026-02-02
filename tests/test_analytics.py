import datetime
import pytest
import uuid
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Competition, Event, Match, Player
from src.services.analytics import AnalyticsService


@pytest.fixture
async def analytics_data(session: AsyncSession):
    # Setup data
    # Team A vs Team B
    comp = Competition(id=1, name="Test Comp", gender="male")
    session.add(comp)

    match = Match(
        id=100,
        competition_id=1,
        season_id=2023,
        match_date=datetime.date(2023, 1, 1),
        home_team="Team A",
        away_team="Team B",
        home_score=1,
        away_score=0
    )
    session.add(match)

    player = Player(id=50, name="Striker One", position="FW")
    session.add(player)

    # Event 1: Shot by Team A (0.5 xG)
    e1 = Event(
        id=uuid.uuid4(), match_id=100, minute=10, second=0, type="Shot",
        player_id=50, team_id=10, location_x=90.0, location_y=40.0,
        attributes={
            "shot_statsbomb_xg": 0.5,
            "team": "Team A",
            "outcome_name": "Goal"
        }
    )
    session.add(e1)

    # Event 2: Shot by Team B (0.3 xG)
    e2 = Event(
        id=uuid.uuid4(), match_id=100, minute=20, second=0, type="Shot",
        player_id=None, team_id=11, location_x=90.0, location_y=40.0,
        attributes={
            "shot_statsbomb_xg": 0.3,
            "team": "Team B"
        }
    )
    session.add(e2)

    # Event 3: Pass by Player One (Successful)
    e3 = Event(
        id=uuid.uuid4(), match_id=100, minute=30, second=0, type="Pass",
        player_id=50, team_id=10, location_x=50.0, location_y=50.0,
        attributes={
            "team": "Team A"
            # No pass_outcome means successful
        }
    )
    session.add(e3)

    # Event 4: Pass by Player One (Failed)
    e4 = Event(
        id=uuid.uuid4(), match_id=100, minute=35, second=0, type="Pass",
        player_id=50, team_id=10, location_x=50.0, location_y=50.0,
        attributes={
            "team": "Team A",
            "pass_outcome": "Incomplete"
        }
    )
    session.add(e4)

    await session.commit()
    return {"match_id": 100, "player_id": 50, "season_id": 2023}


@pytest.mark.asyncio
async def test_get_xg_by_team(session: AsyncSession, analytics_data):
    service = AnalyticsService(session)
    # The fixture data has Team A with 0.5 xG and Team B with 0.3 xG
    result = await service.get_xg_by_team(match_id=100)

    assert "Team A" in result
    assert "Team B" in result
    assert result["Team A"] == 0.5
    assert result["Team B"] == 0.3


@pytest.mark.asyncio
async def test_player_season_stats(session: AsyncSession, analytics_data):
    service = AnalyticsService(session)
    # Ref: src/services/analytics.py uses get_player_season_stats
    stats = await service.get_player_season_stats(player_id=50, season_id=2023)

    assert stats["matches_played"] == 1
    assert stats["total_xg"] == 0.5  # Player 1 (50) had one shot with 0.5
    assert stats["total_passes"] == 2
    assert stats["pass_completion_rate"] == 50.0


@pytest.mark.asyncio
async def test_api_analytics_xg(client: AsyncClient, analytics_data):
    # Ref: src/api/routers/analytics.py prefix="/matches"
    response = await client.get("/matches/100/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["home_xg"] == 0.5
    assert data["away_xg"] == 0.3


@pytest.mark.asyncio
async def test_api_player_stats(client: AsyncClient, analytics_data):
    # Ref: src/api/routers/players.py prefix="/players"
    response = await client.get("/players/50/stats/season/2023")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 50
    assert data["total_xg"] == 0.5
    assert data["pass_completion_rate"] == 50.0
