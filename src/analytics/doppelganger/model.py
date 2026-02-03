from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, ConfigDict, Field
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


class PlayerSeasonVector(BaseModel):
    """
    Metadata entity representing a specific row in the vector matrix.
    Links the abstract math vector back to a human player.
    """

    player_id: int
    season_id: int
    position_group: str
    name: str
    minutes_played: float

    # Allow extra fields safely if schema evolves
    model_config = ConfigDict(extra="ignore")


class PositionModelBundle(BaseModel):
    """
    Container for all artifacts required to run similarity search for a position group.
    Held in memory by the ModelRegistry.
    """

    position_group: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    vector_count: int

    # The Ordered List of Entities (Index i matches Matrix Row i)
    entities: List[PlayerSeasonVector]

    # Scikit-Learn Artifacts
    # We allow arbitrary types because Pydantic doesn't natively validate sklearn
    # objects
    scaler: StandardScaler
    knn: NearestNeighbors
    feature_names: List[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)
