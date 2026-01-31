import pytest


@pytest.mark.asyncio
async def test_create_player(client):
    payload = {"name": "Bruno Fernandes", "position": "Midfielder"}
    # Use /players (no trailing slash) to match router prefix exactly and avoid redirects
    response = await client.post("/players", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Bruno Fernandes"
    assert "id" in data
