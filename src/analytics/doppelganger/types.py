"""
Shared types and enums for the Doppelgänger Engine.
"""

from enum import Enum
from typing import Literal, Tuple

# Entity Key: (Player ID, Season ID, Position Group)
EntityKey = Tuple[int, int, str]


class PositionGroup(str, Enum):
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"


MetricType = Literal["cosine", "euclidean"]
