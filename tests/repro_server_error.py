from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_repro_500():
    # Use the same parameters as the failing request
    response = client.get(
        "/analytics/doppelganger",
        params={"player_id": 10955, "season_id": 282, "limit": 10},
    )
    print(response.text)
    assert response.status_code == 200
