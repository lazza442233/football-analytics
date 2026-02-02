from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.fixture
def mock_arq_pool():
    pool = AsyncMock()
    # Mock enqueue_job return value
    job = MagicMock()
    job.job_id = "test_job_id"
    pool.enqueue_job.return_value = job
    return pool


def test_trigger_ingestion_worker_unavailable():
    # Ensure pool is NOT set
    if hasattr(app.state, "arq_pool"):
        del app.state.arq_pool

    response = client.post(
        "/ingest/", json={"competition_id": 1, "season_id": 1, "ingest_events": True}
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Background worker unavailable"


@pytest.mark.asyncio
async def test_trigger_ingestion_success(mock_arq_pool):
    # Inject mock pool
    app.state.arq_pool = mock_arq_pool

    payload = {"competition_id": 9, "season_id": 281, "ingest_events": True}
    response = client.post("/ingest/", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["job_id"] == "test_job_id"

    mock_arq_pool.enqueue_job.assert_called_once()
    call_args = mock_arq_pool.enqueue_job.call_args
    assert call_args[0][0] == "ingest_season_task"
    assert call_args[1]["_job_id"] == "ingest_season_9_281"
    assert call_args[1]["competition_id"] == 9
