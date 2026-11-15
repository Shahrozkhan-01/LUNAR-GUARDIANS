"""Cached access to NASA's DONKI Solar Energetic Particles and Solar Flares APIs."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import requests

from app.services.nasa_data_processor import (
    MalformedNASAResponse,
    process_nasa_response,
)


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")
NASA_API_BASE_URL = "https://api.nasa.gov/DONKI"
CCMC_API_BASE_URL = "https://ccmc.gsfc.nasa.gov/DONKI-API/get"
DONKI_ENDPOINTS = {
    "SEP": f"{NASA_API_BASE_URL}/SEP",
    "FLR": f"{NASA_API_BASE_URL}/FLR",
}
CCMC_FALLBACK_ENDPOINTS = {
    event_type: f"{CCMC_API_BASE_URL}/{event_type}" for event_type in ("SEP", "FLR")
}
NASA_CACHE_SECONDS = int(os.environ.get("NASA_CACHE_SECONDS", "900"))
NASA_REQUEST_TIMEOUT = (10.0, 20.0)
EVENT_TYPES = ("SEP", "FLR")


class NASAServiceError(RuntimeError):
    """A safe, user-facing description of a failed NASA DONKI request."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def _empty_snapshot() -> Dict[str, Any]:
    return {
        "connection_status": "unavailable",
        "start_date": None,
        "end_date": None,
        "last_updated": None,
        "event_count": 0,
        "events": [],
        "events_by_type": {"SEP": [], "FLR": []},
        "endpoint_status": {
            event_type: {
                "status": "not_checked",
                "error": None,
                "last_updated": None,
            }
            for event_type in EVENT_TYPES
        },
    }


_snapshot = _empty_snapshot()
_expires_at = 0.0
_cache_lock = threading.Lock()
_refresh_lock = threading.Lock()


def _error_message(error: Exception) -> str:
    if isinstance(error, requests.Timeout):
        return "NASA DONKI request timed out."
    if isinstance(error, requests.ConnectionError):
        return "Could not connect to NASA DONKI."
    if isinstance(error, requests.HTTPError):
        response = error.response
        code = response.status_code if response is not None else None
        if code == 401 or code == 403:
            return "NASA rejected the request. Check NASA_API_KEY."
        if code == 429:
            return "NASA DONKI rate limit reached. Try again later."
        if code is not None and code >= 500:
            return "NASA DONKI server returned an error."
        return f"NASA DONKI returned HTTP {code}."
    if isinstance(error, MalformedNASAResponse):
        return "NASA DONKI returned data in an unexpected format."
    return "NASA DONKI request failed."


def _request_events(
    event_type: str, endpoint: str, params: Dict[str, str]
) -> Dict[str, Any]:
    response = requests.get(
        endpoint,
        params=params,
        timeout=NASA_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise MalformedNASAResponse("NASA returned invalid JSON.") from exc
    return {
        "events": process_nasa_response(event_type, payload),
        "error": None,
        "status": "active",
        "source": endpoint,
    }


def _fetch_event_type(
    event_type: str, start_date: str, end_date: str
) -> Dict[str, Any]:
    params = {"startDate": start_date, "endDate": end_date}
    try:
        primary_params = {**params, "api_key": NASA_API_KEY}
        return _request_events(
            event_type,
            DONKI_ENDPOINTS[event_type],
            primary_params,
        )
    except (requests.RequestException, MalformedNASAResponse) as primary_error:
        response = getattr(primary_error, "response", None)
        if response is not None and response.status_code in {401, 403}:
            return {
                "events": [],
                "error": _error_message(primary_error),
                "status": "unavailable",
            }
        try:
            return _request_events(
                event_type,
                CCMC_FALLBACK_ENDPOINTS[event_type],
                params,
            )
        except (requests.RequestException, MalformedNASAResponse) as fallback_error:
            return {
                "events": [],
                "error": _error_message(fallback_error),
                "status": "unavailable",
            }


def get_nasa_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    """Return a cached combined snapshot, refreshing both event types when needed."""
    global _snapshot, _expires_at
    with _cache_lock:
        if not force_refresh and time.monotonic() < _expires_at:
            return deepcopy(_snapshot)

    with _refresh_lock:
        with _cache_lock:
            if not force_refresh and time.monotonic() < _expires_at:
                return deepcopy(_snapshot)
            previous = deepcopy(_snapshot)

        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=6)
        start_date = start.isoformat()
        end_date = end.isoformat()
        refreshed_at = datetime.now(timezone.utc).isoformat()
        events_by_type: Dict[str, list] = {}
        endpoint_status: Dict[str, Dict[str, Optional[str]]] = {}
        successful_count = 0

        with ThreadPoolExecutor(max_workers=len(EVENT_TYPES)) as executor:
            requests_by_type = {
                event_type: executor.submit(
                    _fetch_event_type, event_type, start_date, end_date
                )
                for event_type in EVENT_TYPES
            }

        for event_type in EVENT_TYPES:
            result = requests_by_type[event_type].result()
            old_endpoint = previous["endpoint_status"][event_type]
            if result["status"] == "active":
                successful_count += 1
                events_by_type[event_type] = [
                    {**event, "retrieved_at": refreshed_at}
                    for event in result["events"]
                ]
                endpoint_status[event_type] = {
                    "status": "active",
                    "error": None,
                    "last_updated": refreshed_at,
                    "source": result.get("source"),
                }
            else:
                events_by_type[event_type] = []
                endpoint_status[event_type] = {
                    "status": "unavailable",
                    "error": result["error"],
                    "last_updated": old_endpoint["last_updated"],
                    "source": None,
                }

        events = sorted(
            events_by_type["SEP"] + events_by_type["FLR"],
            key=lambda event: event.get("event_time") or "",
            reverse=True,
        )
        if successful_count == len(EVENT_TYPES):
            connection_status = "active"
        elif successful_count:
            connection_status = "partial"
        else:
            connection_status = "unavailable"

        successful_timestamps = [
            endpoint["last_updated"]
            for endpoint in endpoint_status.values()
            if endpoint["last_updated"]
        ]
        refreshed_snapshot = {
            "connection_status": connection_status,
            "start_date": start_date,
            "end_date": end_date,
            "last_updated": max(successful_timestamps) if successful_timestamps else previous["last_updated"],
            "event_count": len(events),
            "events": events,
            "events_by_type": events_by_type,
            "endpoint_status": endpoint_status,
        }
        with _cache_lock:
            _snapshot = refreshed_snapshot
            _expires_at = time.monotonic() + max(0, NASA_CACHE_SECONDS)
            return deepcopy(_snapshot)


def get_nasa_events(event_type: Optional[str] = None) -> Dict[str, Any]:
    """Return cached events, or a clear service error if requested data is unavailable."""
    if event_type is not None and event_type not in EVENT_TYPES:
        raise ValueError(f"Unsupported NASA DONKI event type: {event_type}")
    snapshot = get_nasa_snapshot()
    if event_type is not None:
        if snapshot["endpoint_status"][event_type]["status"] != "active":
            raise NASAServiceError(
                snapshot["endpoint_status"][event_type]["error"]
                or "NASA DONKI data is temporarily unavailable."
            )
        events = snapshot["events_by_type"][event_type]
    else:
        if snapshot["connection_status"] == "unavailable":
            errors = [
                endpoint["error"]
                for endpoint in snapshot["endpoint_status"].values()
                if endpoint["error"]
            ]
            raise NASAServiceError(
                "; ".join(errors) or "NASA DONKI data is temporarily unavailable."
            )
        events = snapshot["events"]

    return {
        "connection_status": snapshot["connection_status"],
        "start_date": snapshot["start_date"],
        "end_date": snapshot["end_date"],
        "last_updated": snapshot["last_updated"],
        "retrieval_timestamp": snapshot["last_updated"],
        "event_count": len(events),
        "events": deepcopy(events),
        "endpoint_status": deepcopy(snapshot["endpoint_status"]),
    }


def get_solar_flares(force_refresh: bool = False) -> Dict[str, Any]:
    """Return recent real NASA Solar Flare records in the normalized response shape."""
    if force_refresh:
        get_nasa_snapshot(force_refresh=True)
    return get_nasa_events("FLR")


def get_solar_energetic_particles(force_refresh: bool = False) -> Dict[str, Any]:
    """Return recent real NASA SEP records in the normalized response shape."""
    if force_refresh:
        get_nasa_snapshot(force_refresh=True)
    return get_nasa_events("SEP")


def check_nasa_connection(force_refresh: bool = False) -> Dict[str, Any]:
    """Return safe connection state and feed-level errors without credentials."""
    snapshot = get_nasa_snapshot(force_refresh=force_refresh)
    return {
        "connection_status": snapshot["connection_status"],
        "message": (
            "NASA SPACE WEATHER CONNECTION ACTIVE"
            if snapshot["connection_status"] == "active"
            else (
                "NASA DATA PARTIALLY AVAILABLE"
                if snapshot["connection_status"] == "partial"
                else "NASA DATA TEMPORARILY UNAVAILABLE"
            )
        ),
        "last_updated": snapshot["last_updated"],
        "retrieval_timestamp": snapshot["last_updated"],
        "event_count": snapshot["event_count"],
        "start_date": snapshot["start_date"],
        "end_date": snapshot["end_date"],
        "endpoint_status": deepcopy(snapshot["endpoint_status"]),
    }


def get_recent_events(force_refresh: bool = False) -> Dict[str, Any]:
    """Return merged recent SEP and flare records with their retrieval timestamp."""
    if force_refresh:
        get_nasa_snapshot(force_refresh=True)
    return get_nasa_events()


def get_cached_sep_events() -> list:
    """Return only fresh SEP observations; mission advancement never performs I/O."""
    with _cache_lock:
        if (
            time.monotonic() >= _expires_at
            or _snapshot["endpoint_status"]["SEP"]["status"] != "active"
        ):
            return []
        return deepcopy(_snapshot["events_by_type"]["SEP"])


def get_cached_nasa_events() -> list:
    """Return fresh SEP and flare observations; never performs I/O during gameplay."""
    with _cache_lock:
        if time.monotonic() >= _expires_at:
            return []
        return deepcopy(
            _snapshot["events_by_type"]["SEP"]
            + _snapshot["events_by_type"]["FLR"]
        )


def clear_nasa_cache() -> None:
    """Reset cache state for deterministic tests."""
    global _snapshot, _expires_at
    with _refresh_lock:
        with _cache_lock:
            _snapshot = _empty_snapshot()
            _expires_at = 0.0
