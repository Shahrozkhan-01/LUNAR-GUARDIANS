"""Normalize event records returned by NASA DONKI while preserving source data."""

import hashlib
import json
from typing import Any, Dict, List, Optional

from app.services.nasa_event_classifier import classify_nasa_event


class MalformedNASAResponse(ValueError):
    """Raised when a DONKI response does not match the documented list shape."""


def _event_identifier(event_type: str, record: Dict[str, Any]) -> Any:
    if event_type == "FLR":
        return record.get("flrID") or record.get("eventID")
    return record.get("sepID") or record.get("eventID")


def _optional_text(value: Any) -> Optional[str]:
    return value if isinstance(value, str) else None


def _stable_key(event_type: str, record: Dict[str, Any]) -> str:
    source_identity = {
        "event_type": event_type,
        "event_id": _event_identifier(event_type, record),
        "event_time": record.get("eventTime") or record.get("beginTime"),
        "link": record.get("link"),
    }
    if not any(
        source_identity[key]
        for key in ("event_id", "event_time", "link")
    ):
        source_identity["record"] = record
    serialized = json.dumps(source_identity, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_nasa_event(event_type: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Map SEP and FLR fields into one shape without discarding the original."""
    if event_type not in {"SEP", "FLR"}:
        raise ValueError(f"Unsupported DONKI event type: {event_type}")
    if not isinstance(record, dict):
        raise MalformedNASAResponse("Each DONKI event must be a JSON object.")

    event_time = _optional_text(
        record.get("eventTime") if event_type == "SEP" else record.get("beginTime")
    )
    notes = _optional_text(record.get("note"))
    description = _optional_text(record.get("description")) or notes
    linked_events = record.get("linkedEvents")
    instruments = record.get("instruments")

    normalized = {
        "event_type": event_type,
        "event_id": _event_identifier(event_type, record),
        "deduplication_key": _stable_key(event_type, record),
        "event_time": event_time,
        "peak_time": _optional_text(record.get("peakTime")) if event_type == "FLR" else None,
        "end_time": _optional_text(record.get("endTime")) if event_type == "FLR" else None,
        "class_type": _optional_text(record.get("classType")) if event_type == "FLR" else None,
        "linked_events": linked_events if isinstance(linked_events, list) else [],
        "instruments": instruments if isinstance(instruments, list) else [],
        "source_url": record.get("link") if isinstance(record.get("link"), str) else None,
        "description": description if isinstance(description, str) else None,
        "notes": notes if isinstance(notes, str) else None,
        "original": record,
    }
    category, explanation = classify_nasa_event(normalized)
    normalized["category"] = category
    normalized["classification_explanation"] = explanation
    return normalized


def process_nasa_response(event_type: str, payload: Any) -> List[Dict[str, Any]]:
    """Validate a DONKI list response and normalize each source record."""
    if not isinstance(payload, list):
        raise MalformedNASAResponse(
            f"NASA DONKI {event_type} response must be a JSON array."
        )
    if any(not isinstance(record, dict) for record in payload):
        raise MalformedNASAResponse(
            f"NASA DONKI {event_type} response contains a non-object event."
        )
    return [normalize_nasa_event(event_type, record) for record in payload]
