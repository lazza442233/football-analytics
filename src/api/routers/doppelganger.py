"""
API endpoints for the Doppelgänger Engine (Player Similarity Search).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.analytics.doppelganger import schemas
from src.analytics.doppelganger.config import DEFAULT_LIMIT, MAX_LIMIT
from src.analytics.doppelganger.errors import (
    DoppelgangerError,
    InsufficientDataError,
    InvalidPositionError,
    NoMatchesError,
    PlayerSeasonNotFoundError,
)
from src.analytics.doppelganger.service import DoppelgangerService
from src.analytics.doppelganger.types import PositionGroup
from src.database import get_session

router = APIRouter(prefix="/analytics", tags=["Doppelgänger"])


@router.post("/train", status_code=202)
async def train_models(
    season_id: int = Query(..., description="The season ID to train models on"),
    session: AsyncSession = Depends(get_session),
):
    """
    Triggers the training of Doppelgänger models for a specific season.
    This populates the in-memory vector database.
    """
    service = DoppelgangerService(session)
    counts = await service.train_season_models(season_id)

    return {
        "message": "Training complete",
        "season_id": season_id,
        "vector_counts": counts,
    }


@router.get("/doppelganger", response_model=schemas.DoppelgangerResponse)
async def search_similar_players(
    player_id: int = Query(..., description="The target player ID"),
    season_id: int = Query(..., description="The season ID to analyze"),
    position_group: PositionGroup | None = Query(
        None,
        description="Optional position group filter (GK, DEF, MID, FWD). "
        "Defaults to the target player's position.",
    ),
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description=f"Number of similar players to return (max {MAX_LIMIT})",
    ),
    session: AsyncSession = Depends(get_session),
):
    """
    Find players with statistically similar playstyles to a target player.

    The Doppelgänger Engine uses vector similarity search (k-NN with cosine distance)
    to find players who share similar performance characteristics across multiple
    dimensions (possession, attacking, defensive, spatial metrics).

    **How it works:**
    1. Each player-season is represented as a high-dimensional vector ("DNA")
    2. Comparisons respect position groups (you can't compare a GK to a striker)
    3. Returns players with similarity score > 0.70
    4. Includes explanations of shared strengths and key differences

    **Requirements:**
    - Target player must have played at least 180 minutes in the season
    - A trained model must exist for the player's position group

    **Example Response:**
    ```json
    {
      "meta": {
        "model_version": "2026-02-03T04:00:00Z",
        "position_group": "FWD",
        "vector_count": 847
      },
      "target": {
        "name": "Harry Kane",
        "season_id": 2019,
        "position": "FWD"
      },
      "similar_players": [
        {
          "player_id": 123,
          "name": "Roberto Firmino",
          "season_id": 2019,
          "similarity_score": 0.98,
          "explanation": {
            "shared_strengths": ["High progressive_passes_per90", "High pressures"],
            "key_difference": "tackles_per90 differs by 1.20 SD"
          }
        }
      ]
    }
    ```
    """
    # Build query object
    query = schemas.DoppelgangerQuery(
        player_id=player_id,
        season_id=season_id,
        position_group=position_group,
        limit=limit,
    )

    # Execute search
    service = DoppelgangerService(session)

    try:
        result = await service.search_similar_players(query)
        return result

    except PlayerSeasonNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Player {e.player_id} not found for season {e.season_id}. "
            "Ensure the player has event data ingested for this season.",
        )

    except InvalidPositionError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Player {e.player_id} has invalid position group '{e.position}'. "
            "Analysis requires one of: GK, DEF, MID, FWD.",
        )

    except InsufficientDataError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Player {e.player_id} has insufficient data ({e.minutes} minutes). "
            f"Minimum required: {e.min_required} minutes.",
        )

    except NoMatchesError:
        # Return 200 with empty results instead of 404
        # This is a valid state - the player exists but has no similar matches
        return schemas.DoppelgangerResponse(
            meta=schemas.DoppelgangerMeta(
                model_version=schemas.datetime.now(),
                position_group=position_group or "UNKNOWN",
                vector_count=0,
            ),
            target=schemas.TargetPlayer(
                name="Unknown",
                season_id=season_id,
                position=position_group or "UNKNOWN",  # type: ignore
            ),
            similar_players=[],
        )

    except DoppelgangerError as e:
        # Catch-all for other doppelganger-specific errors
        raise HTTPException(status_code=500, detail=str(e))
