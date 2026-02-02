from unittest.mock import patch

import pandas as pd

from src.scripts.research_statsbomb import research_statsbomb


@patch("src.scripts.research_statsbomb.sb")
def test_research_statsbomb(mock_sb, capsys):
    # Setup mock data for competitions
    competitions_df = pd.DataFrame(
        [
            {
                "competition_id": 1,
                "season_id": 2023,
                "competition_name": "Test Competition",
                "season_name": "2023/2024",
                "competition_gender": "male",
                "country_name": "Test Country",
            }
        ]
    )
    mock_sb.competitions.return_value = competitions_df

    # Setup mock data for matches
    matches_df = pd.DataFrame(
        [
            {
                "match_id": 100,
                "match_date": "2023-01-01",
                "home_team": "Team A",
                "away_team": "Team B",
                "home_score": 1,
                "away_score": 0,
                "competition": "Test Competition",
                "season": "2023/2024",
            }
        ]
    )
    mock_sb.matches.return_value = matches_df

    # Setup mock data for events
    events_df = pd.DataFrame(
        [
            {
                "id": "uuid-1",
                "index": 1,
                "period": 1,
                "timestamp": "00:00:00.000",
                "minute": 0,
                "second": 0,
                "type": "Starting XI",
                "possession": 1,
                "possession_team": "Team A",
                "play_pattern": "Regular Play",
                "team": "Team A",
                "duration": 0.0,
                "tactics": None,
                "related_events": None,
                "player": "Player 1",
                "player_id": 1,
                "position": "GK",
                "location": [10.0, 20.0],
                "team_id": 10,
            }
        ]
    )
    mock_sb.events.return_value = events_df

    # Run the function
    research_statsbomb()

    # Verify calls
    mock_sb.competitions.assert_called_once()
    mock_sb.matches.assert_called_once_with(competition_id=1, season_id=2023)
    mock_sb.events.assert_called_once_with(match_id=100)

    # Verify output to stdout contains expected strings
    captured = capsys.readouterr()
    assert "--- 1. Competitions ---" in captured.out
    assert "Selected Competition ID: 1" in captured.out
    assert "--- 2. Matches ---" in captured.out
    assert "Selected Match ID: 100" in captured.out
    assert "--- 3. Events ---" in captured.out
    assert "Sample Location format: [10.0, 20.0]" in captured.out


@patch("src.scripts.research_statsbomb.sb")
def test_research_statsbomb_errors(mock_sb, capsys):
    # Test error handling when competitions fails
    mock_sb.competitions.side_effect = Exception("API Error")

    research_statsbomb()

    captured = capsys.readouterr()
    assert "Error fetching competitions: API Error" in captured.out

    # Reset side effect
    mock_sb.competitions.side_effect = None

    # Test error handling when matches matches returns empty
    competitions_df = pd.DataFrame(
        [
            {
                "competition_id": 1,
                "season_id": 2023,
                "competition_name": "Test Competition",
            }
        ]
    )
    mock_sb.competitions.return_value = competitions_df

    mock_sb.matches.return_value = pd.DataFrame()  # Empty matches

    research_statsbomb()
    captured = capsys.readouterr()
    assert "No matches found for this competition." in captured.out


@patch("src.scripts.research_statsbomb.sb")
def test_research_statsbomb_matches_error(mock_sb, capsys):
    # Test error handling in matches fetch
    competitions_df = pd.DataFrame(
        [
            {
                "competition_id": 1,
                "season_id": 2023,
                "competition_name": "Test Competition",
            }
        ]
    )
    mock_sb.competitions.return_value = competitions_df

    mock_sb.matches.side_effect = Exception("Match API Error")

    research_statsbomb()
    captured = capsys.readouterr()
    assert "Error fetching matches: Match API Error" in captured.out


@patch("src.scripts.research_statsbomb.sb")
def test_research_statsbomb_events_error(mock_sb, capsys):
    # Test error handling in events fetch
    competitions_df = pd.DataFrame(
        [
            {
                "competition_id": 1,
                "season_id": 2023,
                "competition_name": "Test Competition",
            }
        ]
    )
    mock_sb.competitions.return_value = competitions_df

    matches_df = pd.DataFrame([{"match_id": 100, "match_date": "2023-01-01"}])
    mock_sb.matches.return_value = matches_df

    mock_sb.events.side_effect = Exception("Events API Error")

    research_statsbomb()
    captured = capsys.readouterr()
    assert "Error fetching events: Events API Error" in captured.out
