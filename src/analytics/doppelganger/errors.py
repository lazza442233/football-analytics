"""
Custom exceptions for the Doppelgänger Engine.
"""


class DoppelgangerError(Exception):
    """Base exception for Doppelgänger errors."""

    pass


class PlayerSeasonNotFoundError(DoppelgangerError):
    """Raised when the target player/season combination is not found."""

    def __init__(self, player_id: int, season_id: int):
        self.player_id = player_id
        self.season_id = season_id
        super().__init__(f"Player {player_id} not found for season {season_id}")


class InsufficientDataError(DoppelgangerError):
    """Raised when the player has not played enough minutes to be analyzed."""

    def __init__(self, player_id: int, minutes: int, min_required: int):
        self.player_id = player_id
        self.minutes = minutes
        self.min_required = min_required
        super().__init__(
            f"Player {player_id} has insufficient data ({minutes} mins). "
            f"Minimum required: {min_required}"
        )


class NoMatchesError(DoppelgangerError):
    """Raised when no matches satisfy the similarity threshold."""

    def __init__(self, similarity_floor: float):
        super().__init__(f"No matches found above similarity floor {similarity_floor}")
