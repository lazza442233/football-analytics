"""
Configuration constants for the Doppelgänger Engine.
"""

from typing import Dict, List

# Data filtering
MIN_MINUTES: int = 180

# Cosine Query
SIMILARITY_FLOOR: float = 0.70
DISTANCE_CEIL: float = 0.30  # 1 - SIMILARITY_FLOOR

# Pagination
DEFAULT_LIMIT: int = 5
MAX_LIMIT: int = 20

# Operational Safety
MIN_VECTOR_COUNT: int = 50

# --- Feature Engineering Config (The "DNA") ---

# Maps specific player positions to high-level groupings
# Based on StatsBomb/Opta position names
POSITION_MAPPINGS: Dict[str, str] = {
    # Goalkeepers
    "Goalkeeper": "GK",
    # Defenders
    "Right Back": "DEF",
    "Left Back": "DEF",
    "Center Back": "DEF",
    "Right Center Back": "DEF",
    "Left Center Back": "DEF",
    "Right Wing Back": "DEF",
    "Left Wing Back": "DEF",
    # Midfielders
    "Center Defensive Midfield": "MID",
    "Right Defensive Midfield": "MID",
    "Left Defensive Midfield": "MID",
    "Center Midfield": "MID",
    "Right Midfield": "MID",
    "Left Midfield": "MID",
    "Right Center Midfield": "MID",
    "Left Center Midfield": "MID",
    "Center Attacking Midfield": "MID",
    "Right Attacking Midfield": "MID",
    "Left Attacking Midfield": "MID",
    # Forwards
    "Right Wing": "FWD",
    "Left Wing": "FWD",
    "Right Center Forward": "FWD",
    "Left Center Forward": "FWD",
    "Center Forward": "FWD",
    "Secondary Striker": "FWD",
}

# Maps raw Event.type to internal feature names
EVENT_TYPE_MAPPINGS: Dict[str, str] = {
    "Pass": "passes_attempted",
    "Shot": "shots_total",
    "Dribble": "dribbles_attempted",
    "Interception": "interceptions",
    "Pressure": "pressures_applied",
    "Tackle": "tackles",
}

# Metrics that should be normalized per 90 minutes
# Naming Convention: All normalized metrics must end in "_p90"
NORMALIZE_PER_90_COLS: List[str] = [
    "passes_attempted",
    "passes_completed",
    "progressive_passes",
    "shot_assists",
    "progressive_carries",
    "carry_distance",
    "shots_total",
    "xg_total",
    "dribbles_attempted",
    "interceptions",
    "pressures_applied",
    "tackles",
]
