"""
Configuration constants for the Doppelgänger Engine.
"""

# Data filtering
MIN_MINUTES: int = 300

# Cosine Query
SIMILARITY_FLOOR: float = 0.70
DISTANCE_CEIL: float = 0.30  # 1 - SIMILARITY_FLOOR

# Pagination
DEFAULT_LIMIT: int = 5
MAX_LIMIT: int = 20

# Operational Safety
MIN_VECTOR_COUNT: int = 50
