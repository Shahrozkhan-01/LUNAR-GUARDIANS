"""
LUNAR GUARDIANS — Game Simulation API Routes.

Endpoints:
- POST /api/game/start
- GET  /api/game/{mission_id}
- POST /api/game/{mission_id}/action
- POST /api/game/{mission_id}/advance
- GET  /api/game/{mission_id}/events
- POST /api/game/{mission_id}/power
"""

from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    ActionResponse,
    AdvanceDayResponse,
    EventsListResponse,
    ExecuteActionRequest,
    GameState,
    PowerUpdateRequest,
    StartMissionRequest,
)
from app.services import simulation

router = APIRouter(prefix="/api/game", tags=["Game Simulation"])


@router.post(
    "/start",
    response_model=GameState,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize a new lunar mission",
)
async def start_mission(payload: StartMissionRequest) -> GameState:
    return simulation.create_mission(payload)


@router.get(
    "/{mission_id}",
    response_model=GameState,
    summary="Fetch current mission state",
)
async def get_mission_state(mission_id: str) -> GameState:
    try:
        return simulation.get_mission_or_error(mission_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "/{mission_id}/action",
    response_model=ActionResponse,
    summary="Execute a player action or event decision",
)
async def run_player_action(mission_id: str, payload: ExecuteActionRequest) -> ActionResponse:
    try:
        return simulation.execute_player_action(mission_id, payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post(
    "/{mission_id}/advance",
    response_model=AdvanceDayResponse,
    summary="Advance the lunar simulation by one day",
)
async def advance_day(mission_id: str) -> AdvanceDayResponse:
    try:
        return simulation.advance_mission_day(mission_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get(
    "/{mission_id}/events",
    response_model=EventsListResponse,
    summary="Fetch active simulated training events",
)
async def get_mission_events(mission_id: str) -> EventsListResponse:
    try:
        state = simulation.get_mission_or_error(mission_id)
        return EventsListResponse(
            mission_id=state.mission_id,
            active_events=state.active_events,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "/{mission_id}/power",
    response_model=GameState,
    summary="Validate and update electricity allocation across outpost systems",
)
async def set_power_allocation(mission_id: str, payload: PowerUpdateRequest) -> GameState:
    try:
        updated_state, _ = simulation.update_power_allocation(mission_id, payload)
        return updated_state
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
