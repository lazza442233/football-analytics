from typing import Dict, Optional

from src.analytics.doppelganger.model import PositionModelBundle


class ModelRegistry:
    """
    Singleton-ish container that holds the in-memory models for all position groups.
    """

    def __init__(self):
        self._bundles: Dict[str, PositionModelBundle] = {}

    def register(self, position_group: str, bundle: PositionModelBundle) -> None:
        """
        Stores a trained bundle. Overwrites existing if present.
        """
        self._bundles[position_group] = bundle

    def get(self, position_group: str) -> Optional[PositionModelBundle]:
        """
        Retrieves the bundle for a position group.
        """
        return self._bundles.get(position_group)

    def clear(self) -> None:
        self._bundles.clear()

    @property
    def status(self) -> Dict[str, int]:
        """Returns map of position_group -> vector_count"""
        return {k: v.vector_count for k, v in self._bundles.items()}


# Global instance for the service to import
registry = ModelRegistry()
