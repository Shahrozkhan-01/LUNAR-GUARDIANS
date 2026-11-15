"""NASA DONKI read-only routes."""

from fastapi import APIRouter, HTTPException, Query

from app.services import nasa_service


router = APIRouter(prefix="/api/nasa", tags=["NASA Space Weather"])


@router.get("/status", summary="Get NASA DONKI connection and cache status")
def nasa_status(refresh: bool = Query(default=False)) -> dict:
    return nasa_service.check_nasa_connection(force_refresh=refresh)


@router.get("/events", summary="Get all recent normalized DONKI events")
@router.get("/solar-events", summary="Get normalized DONKI SEP and solar-flare events")
def solar_events(refresh: bool = Query(default=False)) -> dict:
    try:
        return nasa_service.get_recent_events(force_refresh=refresh)
    except nasa_service.NASAServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "message": str(exc),
                "connection_status": "unavailable",
            },
        ) from exc


@router.get("/sep", summary="Get normalized Solar Energetic Particle events")
def sep_events(refresh: bool = Query(default=False)) -> dict:
    try:
        return nasa_service.get_solar_energetic_particles(force_refresh=refresh)
    except nasa_service.NASAServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": str(exc), "event_type": "SEP"},
        ) from exc


@router.get("/flares", summary="Get normalized Solar Flare events")
def flare_events(refresh: bool = Query(default=False)) -> dict:
    try:
        return nasa_service.get_solar_flares(force_refresh=refresh)
    except nasa_service.NASAServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": str(exc), "event_type": "FLR"},
        ) from exc


@router.get("/last-updated", summary="Get the last successful NASA data retrieval time")
def nasa_last_updated() -> dict:
    status = nasa_service.check_nasa_connection()
    return {
        "last_updated": status["last_updated"],
        "retrieval_timestamp": status["retrieval_timestamp"],
        "connection_status": status["connection_status"],
    }
