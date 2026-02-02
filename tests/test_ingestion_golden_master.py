import uuid
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlmodel import select

from src.models import Competition, Event, Match, Player
from src.services.ingestion import StatsBombIngestionService


@pytest.fixture
def mock_sb_data():
    """Golden Master Data Fixtures"""

    # Competition Data
    competitions_df = pd.DataFrame(
        [
            {
                "competition_id": 999,
                "season_id": 1,
                "competition_name": "Golden League",
                "competition_gender": "male",
                "country_name": "Testland",
            }
        ]
    )

    # Match Data
    matches_df = pd.DataFrame(
        [
            {
                "match_id": 1001,
                "match_date": "2024-01-01",
                "kick_off": "15:00:00.000",
                "home_team": "Golden Team A",
                "away_team": "Golden Team B",
                "home_score": 2,
                "away_score": 1,
                "competition": 999,
                "season": 1,
            }
        ]
    )

    # Events Data
    # 1. Start of match
    # 2. Pass
    # 3. Shot (Goal)
    events_df = pd.DataFrame(
        [
            {
                "id": str(uuid.uuid4()),
                "match_id": 1001,
                "minute": 0,
                "second": 1,
                "type": "Pass",
                "player_id": 10,
                "player": "Player A1",
                "position": "Midfielder",
                "team_id": 100,
                "team": "Golden Team A",
                "location": [60.0, 40.0],
                "pass_length": 15.0,
                "pass_angle": 0.5,
            },
            {
                "id": str(uuid.uuid4()),
                "match_id": 1001,
                "minute": 25,
                "second": 30,
                "type": "Shot",
                "player_id": 11,
                "player": "Player A2",
                "position": "Striker",
                "team_id": 100,
                "team": "Golden Team A",
                "location": [105.0, 35.0],
                "shot_statsbomb_xg": 0.35,
                "shot_outcome": "Goal",
            },
        ]
    )

    return {"competitions": competitions_df, "matches": matches_df, "events": events_df}


@pytest.mark.asyncio
async def test_golden_master_ingestion(session, mock_sb_data):
    """
    Golden Master Test:
    Simulates a full ingestion pipeline with known, fixed data.
    Asserts that the data is correctly transformed and persisted.
    """

    # 1. Setup Service
    service = StatsBombIngestionService(
        competition_id=999, season_id=1, team_name="Golden Team A"
    )

    # 2. Patch External API calls
    # We patch 'src.services.ingestion.sb' because that's where it's imported
    with patch("src.services.ingestion.sb") as mock_sb:
        mock_sb.competitions = MagicMock(return_value=mock_sb_data["competitions"])
        # sb.matches and sb.events are called as functions, return DataFrames
        mock_sb.matches = MagicMock(return_value=mock_sb_data["matches"])
        mock_sb.events = MagicMock(return_value=mock_sb_data["events"])

        # 3. Execution (Simulating the flow)

        # A. Ingest Competition
        comp = await service.ingest_competition()
        assert comp is not None
        assert comp.name == "Golden League"

        # Verify DB
        db_comp = await session.get(Competition, 999)
        assert db_comp is not None
        assert db_comp.name == "Golden League"

        # B. Ingest Match
        match = await service.ingest_match(comp)
        assert match is not None
        assert match.home_team == "Golden Team A"
        assert match.home_score == 2

        # Verify DB
        db_match = await session.get(Match, 1001)
        assert db_match is not None
        assert db_match.season_id == 1
        assert db_match.away_team == "Golden Team B"

        # C. Ingest Events
        await service.ingest_events(match.id)

        # Verify DB - Players
        # Player A1 (ID 10) and Player A2 (ID 11) should exist
        p1 = await session.get(Player, 10)
        p2 = await session.get(Player, 11)
        assert p1 is not None and p1.name == "Player A1"
        assert p2 is not None and p2.name == "Player A2"

        # Verify DB - Events
        # We expect 2 events
        result = await session.execute(select(Event).where(Event.match_id == 1001))
        events = result.scalars().all()
        assert len(events) == 2

        # Check specific event details (The "Type" check)
        shot_events = [e for e in events if e.type == "Shot"]
        assert len(shot_events) == 1
        shot = shot_events[0]

        # Check JSONB attributes (The "Detail" check)
        # Note: StatsBombIngestionService.clean_dict removes NaNs and core fields.
        # "shot_statsbomb_xg" and "shot_outcome" should remain in attributes
        assert shot.attributes.get("shot_outcome") == "Goal"
        assert shot.attributes.get("shot_statsbomb_xg") == 0.35
        assert shot.player_id == 11
        assert shot.location_x == 105.0
