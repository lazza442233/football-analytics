import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.asyncio
async def test_get_match_xg_404(client: AsyncClient):
    response = await client.get("/matches/999999/analytics/summary")
    assert response.status_code == 404
    assert response.json()["detail"] == "Match not found"


@pytest.mark.asyncio
async def test_get_player_season_stats_empty(client: AsyncClient):
    # The service returns zeros instead of None when no data is found,
    # so it returns 200 OK
    response = await client.get("/players/999999/stats/season/2023")
    assert response.status_code == 200
    data = response.json()
    assert data["matches_played"] == 0
    assert data["player_id"] == 999999


@pytest.mark.asyncio
async def test_search_match_events_404(client: AsyncClient):
    # This endpoint currently returns empty list, not 404,
    # but let's verify that behavior
    response = await client.get("/matches/999999/events/search")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_search_match_events_filters(client: AsyncClient, session: AsyncSession):
    # Depending on data availability, just exercizing the query params
    response = await client.get(
        "/matches/100/events/search?min_minute=10&max_minute=50"
    )
    assert response.status_code == 200

    response = await client.get("/matches/100/events/search?type=Shot")
    assert response.status_code == 200
