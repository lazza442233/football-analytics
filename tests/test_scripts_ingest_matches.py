import sys
from unittest.mock import MagicMock, patch

from src.scripts.ingest_matches import main


@patch("src.scripts.ingest_matches.StatsBombIngestionService")
@patch("src.scripts.ingest_matches.asyncio.run")
def test_ingest_matches_script_success(mock_asyncio_run, mock_service_cls):
    # Setup mocks
    mock_service_instance = MagicMock()
    mock_service_instance.ingest_season_matches.return_value = True
    mock_service_cls.return_value = mock_service_instance

    # Mock sys.argv
    with patch.object(
        sys, "argv", ["ingest_matches", "--comp-id", "43", "--season-id", "3"]
    ):
        main()

    # Verify
    mock_service_cls.assert_called_once()
    mock_service_instance.ingest_season_matches.assert_called_once_with(
        competition_id=43, season_id=3, ingest_events=False
    )
    mock_asyncio_run.assert_called_once()


@patch("src.scripts.ingest_matches.StatsBombIngestionService")
@patch("src.scripts.ingest_matches.asyncio.run")
def test_ingest_matches_script_with_events(mock_asyncio_run, mock_service_cls):
    mock_service_instance = MagicMock()
    mock_service_cls.return_value = mock_service_instance

    with patch.object(
        sys,
        "argv",
        ["ingest_matches", "--comp-id", "43", "--season-id", "3", "--events"],
    ):
        main()

    mock_service_instance.ingest_season_matches.assert_called_once_with(
        competition_id=43, season_id=3, ingest_events=True
    )
