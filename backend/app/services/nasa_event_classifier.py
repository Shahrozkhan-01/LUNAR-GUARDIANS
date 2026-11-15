"""Conservative, educational labels for NASA DONKI event records.

These rules describe what a DONKI record supports, not crew or lunar-surface
radiation risk. Adjust the policy constants only when the evidence threshold is
reviewed; never translate flare class into radiation dose.
"""

from datetime import datetime
from typing import Dict, Tuple


INSUFFICIENT_DATA = "INSUFFICIENT DATA FOR RISK ASSESSMENT"

CLASSIFICATION_RULES: Dict[str, Dict[str, str]] = {
    "SEP": {
        "category": INSUFFICIENT_DATA,
        "reason": (
            "DONKI reports a Solar Energetic Particle event, but this record does "
            "not provide a lunar surface dose or enough particle-flux information "
            "to estimate astronaut exposure."
        ),
    },
    "FLR": {
        "category": "INFORMATIONAL",
        "reason": (
            "This is a NASA solar-flare report. A flare class describes the flare's "
            "X-ray brightness, not an astronaut's radiation dose."
        ),
    },
}


def classify_nasa_event(event: Dict) -> Tuple[str, str]:
    """Return a conservative category and an explanation for a normalized event."""
    event_type = event.get("event_type")
    event_time = event.get("event_time")
    if not _has_valid_event_time(event_time):
        return (
            INSUFFICIENT_DATA,
            "The NASA record has no usable event time, so it cannot be assessed "
            "or used to create a timed learning scenario.",
        )

    rule = CLASSIFICATION_RULES.get(event_type)
    if rule is None:
        return (
            INSUFFICIENT_DATA,
            "This event type is not covered by the educational classification rules.",
        )

    return rule["category"], rule["reason"]


def is_eligible_nasa_event(event: Dict) -> bool:
    """Only dated SEP or flare records can create a monitoring scenario."""
    if event.get("event_type") not in {"SEP", "FLR"} or not event.get("deduplication_key"):
        return False
    return _has_valid_event_time(event.get("event_time"))


def is_eligible_sep_for_scenario(event: Dict) -> bool:
    """Compatibility helper for callers that specifically need SEP eligibility."""
    return event.get("event_type") == "SEP" and is_eligible_nasa_event(event)


def _has_valid_event_time(event_time: object) -> bool:
    if not isinstance(event_time, str) or not event_time:
        return False
    try:
        datetime.fromisoformat(event_time.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
