"""
Pydantic schemas for API request/response contracts.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.analytics.doppelganger.config import DEFAULT_LIMIT, MAX_LIMIT
from src.analytics.doppelganger.types import PositionGroup


class DoppelgangerQuery(BaseModel):
    player_id: int
    season_id: int
    position_group: Optional[PositionGroup] = None
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    exclude_same_player: bool = Field(
        default=True,
        description="Exclude matches of the same player from different seasons",
    )

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        if v > MAX_LIMIT:
            return MAX_LIMIT
        return v


class DoppelgangerMeta(BaseModel):
    model_version: datetime
    position_group: str
    vector_count: int


class TargetPlayer(BaseModel):
    name: str = "Unknown"  # Fallback for when basic info isn't pre-fetched properly
    season_id: int
    position: PositionGroup


class SimilarPlayerExplanation(BaseModel):
    shared_strengths: List[str]
    key_difference: Optional[str] = None


class SimilarPlayerResult(BaseModel):
    player_id: int
    name: str
    season_id: int
    similarity_score: float
    explanation: SimilarPlayerExplanation


class DoppelgangerResponse(BaseModel):
    meta: DoppelgangerMeta
    target: TargetPlayer
    similar_players: List[SimilarPlayerResult]
