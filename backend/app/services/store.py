"""
LUNAR GUARDIANS — Separate Game State Repository.

Uses an in-memory dictionary for the current prototype while keeping storage
cleanly decoupled from simulation services so SQLite persistence can be swapped
in seamlessly in a future phase.
"""

from copy import deepcopy
from typing import Dict, Optional
from app.models.schemas import GameState


class InMemoryMissionStore:
    def __init__(self) -> None:
        self._missions: Dict[str, GameState] = {}

    def save(self, state: GameState) -> GameState:
        stored = deepcopy(state)
        self._missions[state.mission_id] = stored
        return deepcopy(stored)

    def get(self, mission_id: str) -> Optional[GameState]:
        found = self._missions.get(mission_id)
        return deepcopy(found) if found is not None else None

    def clear(self) -> None:
        self._missions.clear()


mission_store = InMemoryMissionStore()
