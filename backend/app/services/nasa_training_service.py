"""Build optional training-event context from existing NASA dataset products."""

import math
from typing import Any, Dict, List, Optional, Tuple

from app.models.schemas import (
    EventDecisionOption,
    NasaTrainingDataContext,
    NasaTrainingEvent,
)
from app.services import dataset_service
from app.services.nasa_event_classifier import is_eligible_sep_for_scenario
from app.services.nasa_service import get_cached_nasa_events


DATASET_NAMES = {
    "diviner": "Diviner Lunar Radiometer",
    "lola": "LOLA Lunar Elevation",
    "ace_epam": "ACE EPAM",
    "stereo_impact": "STEREO-A IMPACT",
    "jpl_horizons": "JPL Horizons Earth-Moon",
}

UNAVAILABLE_NOTE = (
    "No replacement NASA measurements were generated. This training scenario "
    "remains available using its labeled educational description."
)


def _dataset_snapshot(dataset_id: str) -> Optional[Dict[str, Any]]:
    try:
        metadata = dataset_service.get_dataset_metadata(dataset_id)
        if metadata.get("availability", {}).get("status") != "available":
            return None
        summary = dataset_service.get_dataset_summary(dataset_id)
        if summary.get("availability", {}).get("status") != "available":
            return None
        return {
            "metadata": metadata,
            "summary": summary.get("summary", {}),
        }
    except dataset_service.DatasetServiceError:
        return None


def _record_page(dataset_id: str) -> List[Dict[str, Any]]:
    try:
        response = dataset_service.get_dataset_records(
            dataset_id, page=1, page_size=50
        )
    except dataset_service.DatasetServiceError:
        return []
    records = response.get("records", [])
    return records if isinstance(records, list) else []


def _source_fields(
    dataset_id: str, snapshot: Dict[str, Any]
) -> Dict[str, Optional[str]]:
    metadata = snapshot["metadata"]
    source = metadata.get("source") or {}
    urls = source.get("urls") or []
    return {
        "dataset_id": dataset_id,
        "dataset_name": DATASET_NAMES[dataset_id],
        "source": source.get("organization") or "NASA dataset catalog",
        "source_url": urls[0] if urls else None,
    }


def _point(
    dataset_id: str,
    snapshot: Dict[str, Any],
    *,
    data_label: str,
    measurement: str,
    value: Any,
    unit: Optional[str],
    date_or_coverage: Optional[str],
    note: Optional[str] = None,
) -> NasaTrainingDataContext:
    return NasaTrainingDataContext(
        **_source_fields(dataset_id, snapshot),
        data_label=data_label,
        measurement=measurement,
        value=str(value),
        unit=unit,
        date_or_coverage=date_or_coverage,
        note=note,
    )


def _numeric(value: Any) -> Optional[float]:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _diviner_context() -> List[NasaTrainingDataContext]:
    snapshot = _dataset_snapshot("diviner")
    if snapshot is None:
        return []
    columns = snapshot["summary"].get("columns") or {}
    tbol = columns.get("tbol") or {}
    mean = tbol.get("mean")
    if mean is None:
        return []
    return [
        _point(
            "diviner",
            snapshot,
            data_label="DERIVED VALUE",
            measurement="Bolometric average calibrated brightness temperature (mean summary)",
            value=mean,
            unit=tbol.get("unit"),
            date_or_coverage=snapshot["metadata"].get("coverage"),
            note=(
                "A statistic from the historical gridded product; it is not live "
                "habitat or astronaut temperature."
            ),
        )
    ]


def _lola_context() -> List[NasaTrainingDataContext]:
    snapshot = _dataset_snapshot("lola")
    if snapshot is None:
        return []
    statistics = snapshot["summary"].get(
        "height_m_relative_to_reference_radius_statistics"
    ) or {}
    mean = statistics.get("height_m_mean")
    if mean is None:
        return []
    return [
        _point(
            "lola",
            snapshot,
            data_label="DERIVED VALUE",
            measurement="Global mean elevation relative to the reference radius",
            value=mean,
            unit="m",
            date_or_coverage=snapshot["metadata"].get("coverage"),
            note=(
                "Global summary, not a south-polar site elevation or detailed "
                "landing-hazard information."
            ),
        )
    ]


def _ace_context() -> List[NasaTrainingDataContext]:
    snapshot = _dataset_snapshot("ace_epam")
    if snapshot is None:
        return []
    metadata = snapshot["metadata"].get("processing_metadata") or {}
    variables = metadata.get("variables") or {}
    records = _record_page("ace_epam")
    for variable_name in ("P7", "P8"):
        variable = variables.get(variable_name) or {}
        for record in records:
            measurement = (record.get("measurements") or {}).get(variable_name) or {}
            value = measurement.get("value")
            if not measurement.get("valid") or _numeric(value) is None:
                continue
            return [
                _point(
                    "ace_epam",
                    snapshot,
                    data_label="REAL NASA DATA",
                    measurement=variable.get("official_long_description")
                    or variable.get("description")
                    or f"ACE EPAM {variable_name} particle-channel value",
                    value=value,
                    unit=variable.get("units"),
                    date_or_coverage=record.get("timestamp_utc"),
                    note=(
                        "Historical measurement at ACE, not a lunar-surface "
                        "measurement or astronaut radiation dose."
                    ),
                )
            ]
    return []


def _stereo_context() -> List[NasaTrainingDataContext]:
    snapshot = _dataset_snapshot("stereo_impact")
    if snapshot is None:
        return []
    records = _record_page("stereo_impact")
    measurement_units = (
        snapshot["summary"].get("intensity_units")
        or "particles/(cm^2-sr-sec-MeV)"
    )
    contexts: List[NasaTrainingDataContext] = []
    for kind in ("electron", "proton"):
        field = next(
            (
                key
                for key in (records[0] if records else {})
                if key.startswith(f"intensity_{kind}_")
            ),
            None,
        )
        if field is None:
            continue
        value = next(
            (
                record.get(field)
                for record in records
                if _numeric(record.get(field)) is not None
            ),
            None,
        )
        if value is None:
            continue
        first_record = next(
            record for record in records if _numeric(record.get(field)) is not None
        )
        channel = field.removeprefix("intensity_")
        contexts.append(
            _point(
                "stereo_impact",
                snapshot,
                data_label="REAL NASA DATA",
                measurement=f"STEREO-A IMPACT {kind} channel ({channel})",
                value=value,
                unit=measurement_units,
                date_or_coverage=first_record.get("record_start_utc"),
                note=(
                    "Historical STEREO-A spacecraft measurement, not a lunar "
                    "surface measurement or astronaut radiation dose."
                ),
            )
        )
    return contexts


def _horizons_context() -> List[NasaTrainingDataContext]:
    snapshot = _dataset_snapshot("jpl_horizons")
    if snapshot is None:
        return []
    records = _record_page("jpl_horizons")
    if not records:
        return []
    record = records[0]
    timestamp = record.get("epoch_utc")
    units = snapshot["summary"].get("units") or {}
    fields = (
        (
            "COMPUTED EPHEMERIS",
            "Earth-Moon range",
            record.get("earth_moon_range_km"),
            units.get("earth_moon_range_km", "km"),
            "Calculated Horizons ephemeris value.",
        ),
        (
            "COMPUTED EPHEMERIS",
            "One-way down-leg light time",
            record.get("one_way_down_leg_light_time_minutes"),
            units.get("one_way_down_leg_light_time_minutes", "min"),
            "One-way vacuum light time only; network and processing delays are not included.",
        ),
        (
            "DERIVED VALUE",
            "Two-way vacuum light time",
            record.get("two_way_vacuum_light_time_seconds_derived"),
            units.get("two_way_vacuum_light_time_seconds_derived", "s"),
            "Derived two-way vacuum value; it is not a direct Horizons measurement.",
        ),
    )
    return [
        _point(
            "jpl_horizons",
            snapshot,
            data_label=data_label,
            measurement=measurement,
            value=value,
            unit=unit,
            date_or_coverage=timestamp,
            note=note,
        )
        for data_label, measurement, value, unit, note in fields
        if value is not None
    ]


def _decision(
    choice_id: str,
    label: str,
    cost_text: str,
    consequence_text: str,
    rationale: str,
    required_resources: Optional[Dict[str, float]] = None,
) -> EventDecisionOption:
    return EventDecisionOption(
        choice_id=choice_id,
        label=label,
        cost_text=cost_text,
        consequence_text=consequence_text,
        rationale=rationale,
        required_resources=required_resources or {},
    )


def _availability(count: int, expected: int) -> str:
    if count == 0:
        return "unavailable"
    return "available" if count >= expected else "partial"


def _unavailable_note(missing: List[str]) -> Optional[str]:
    if not missing:
        return None
    return (
        f"Some NASA context is unavailable ({', '.join(missing)}). "
        + UNAVAILABLE_NOTE
    )


def build_nasa_training_events(
    mission_id: str, day: int
) -> Tuple[List[NasaTrainingEvent], List[str]]:
    """Create one optional event per category using only available cached data."""
    diviner = _diviner_context()
    lola = _lola_context()
    ace = _ace_context()
    stereo = _stereo_context()
    horizons = _horizons_context()

    sep_events = [
        event
        for event in get_cached_nasa_events()
        if event.get("event_type") == "SEP"
        and is_eligible_sep_for_scenario(event)
    ]
    latest_sep = sep_events[0] if sep_events else None
    seen_event_ids: List[str] = []
    space_weather_context = ace + stereo
    space_weather_description = (
        "No suitable cached DONKI SEP event was available when this mission "
        "started. This is a SIMULATED TRAINING EVENT, not a NASA alert."
    )
    if latest_sep:
        event_id = latest_sep.get("event_id")
        deduplication_key = latest_sep.get("deduplication_key")
        if deduplication_key:
            seen_event_ids.append(deduplication_key)
        space_weather_context.append(
            NasaTrainingDataContext(
                dataset_id="donki_sep",
                data_label="REAL NASA DATA",
                dataset_name="NASA DONKI Solar Energetic Particles",
                source="NASA DONKI",
                source_url=latest_sep.get("source_url"),
                measurement=(
                    f"Reported {latest_sep.get('event_type') or 'SEP'} event"
                ),
                value=str(event_id or "Event ID not supplied"),
                date_or_coverage=latest_sep.get("event_time"),
                note=(
                    "This event metadata is shown as context only; it is not a "
                    "lunar radiation-dose measurement."
                ),
            )
        )
        space_weather_description = (
            "A cached real NASA DONKI SEP record is included as educational "
            "context. The player choices below are a SIMULATED TRAINING EVENT, "
            "not a real-time NASA alert or radiation-dose assessment."
        )

    environment_context = diviner + lola
    communication_context = horizons
    missing_environment = []
    if not diviner:
        missing_environment.append("Diviner")
    if not lola:
        missing_environment.append("LOLA")
    missing_space_weather = []
    if not ace:
        missing_space_weather.append("ACE EPAM")
    if len(stereo) < 2:
        missing_space_weather.append("STEREO-A electron/proton sample")
    missing_communication = (
        ["JPL Horizons range/light-time records"]
        if len(communication_context) < 3
        else []
    )
    training_events = [
        NasaTrainingEvent(
            event_id=f"nasa-training-south-polar-{mission_id}",
            category="south_polar_environment",
            title="South Polar Environment Challenge",
            description=(
                "Plan how the outpost team will prepare for environmental and "
                "terrain-related operational questions."
            ),
            scientific_context=(
                "Historical Diviner brightness-temperature summaries and broad "
                "LOLA elevation context are separate datasets with distinct "
                "coverage dates. Neither describes live habitat conditions."
            ),
            data_availability=_availability(len(environment_context), 2),
            data_unavailable_note=_unavailable_note(missing_environment),
            data_context=environment_context,
            scientific_limitations=[
                "Diviner brightness temperature is historical surface context, not live habitat temperature.",
                "LOLA global elevation is broad terrain context, not detailed landing-hazard information.",
                "The dataset summaries do not directly calculate game resource use.",
            ],
            decisions=[
                _decision(
                    "environment_power_plan",
                    "Review the habitat power-reserve plan",
                    "Costs 2 simulated Power units",
                    "Uses 2 simulated Power and earns 3 practice Science points.",
                    "Power planning helps teams prepare for environmental uncertainty without treating a historical temperature statistic as a habitat reading.",
                    {"power": 2.0},
                ),
                _decision(
                    "environment_terrain_review",
                    "Schedule a broad terrain-context review",
                    "Costs 3 simulated Power units",
                    "Uses 3 simulated Power and earns 4 practice Science points.",
                    "Broad elevation context can inform route planning, but a detailed landing assessment needs higher-resolution hazard data.",
                    {"power": 3.0},
                ),
                _decision(
                    "environment_keep_plan",
                    "Keep the current plan and record the limitations",
                    "No resource cost",
                    "No resource change; earns 1 practice Science point.",
                    "Recognizing what a dataset cannot tell you is part of responsible mission planning.",
                ),
            ],
            day_triggered=day,
        ),
        NasaTrainingEvent(
            event_id=f"nasa-training-space-weather-{mission_id}",
            category="space_weather_preparedness",
            title="Space Weather Preparedness",
            description=space_weather_description,
            scientific_context=(
                "DONKI reports event metadata; ACE EPAM and STEREO-A provide "
                "historical spacecraft measurements from their own observation "
                "dates. These records are not a single simultaneous event or "
                "current lunar conditions."
            ),
            data_availability=_availability(len(space_weather_context), 3),
            data_unavailable_note=_unavailable_note(missing_space_weather),
            data_context=space_weather_context,
            scientific_limitations=[
                "ACE EPAM and STEREO-A measurements are from spacecraft, not the lunar surface.",
                "Neither spacecraft dataset measures astronaut radiation dose.",
                "Historical measurements do not establish current conditions at the Moon.",
                "A DONKI SEP record does not provide lunar surface dosimetry.",
            ],
            decisions=[
                _decision(
                    "space_weather_shelter",
                    "Enter simulated protected-operation mode",
                    "Costs 10 simulated Power units",
                    "Uses the existing radiation-shelter mechanic; changes to shield and exposure indicators are simulated.",
                    "Shelter procedures are a useful preparedness topic; the historical data does not determine the fictional game effect.",
                    {"power": 10.0},
                ),
                _decision(
                    "space_weather_pause_activity",
                    "Postpone an optional outdoor activity",
                    "No resource cost",
                    "No resource change; up to 2 practice Science points are deferred.",
                    "A mission team can review plans when space-weather information warrants attention, without claiming a measured crew dose.",
                ),
                _decision(
                    "space_weather_monitor",
                    "Continue with a simulated monitoring plan",
                    "Costs 2 simulated Power units",
                    "Uses 2 simulated Power and earns 3 practice Science points.",
                    "Monitoring is an educational choice; no particle flux is converted to crew exposure.",
                    {"power": 2.0},
                ),
            ],
            day_triggered=day,
        ),
        NasaTrainingEvent(
            event_id=f"nasa-training-communication-{mission_id}",
            category="earth_moon_communication",
            title="Earth-Moon Communication Challenge",
            description=(
                "Plan an outpost communication session using the saved "
                "Earth-Moon Horizons ephemeris values."
            ),
            scientific_context=(
                "The displayed Horizons range and one-way light time are "
                "computed ephemerides for the recorded epoch; future epochs "
                "are calculated predictions, not observations. The two-way "
                "vacuum light time is derived separately; none includes "
                "network or processing delay."
            ),
            data_availability=_availability(len(communication_context), 3),
            data_unavailable_note=_unavailable_note(missing_communication),
            data_context=communication_context,
            scientific_limitations=[
                "Horizons values are computed ephemerides, not observations.",
                "Only use these values for their recorded epoch and coverage.",
                "One-way light time is not total communication delay.",
                "Two-way vacuum light time is derived; network and processing delays are not included.",
            ],
            decisions=[
                _decision(
                    "communication_wait",
                    "Wait for a complete response before proceeding",
                    "Costs 2 simulated Power units",
                    "Uses 2 simulated Power and earns 2 practice Science points.",
                    "Allowing for signal travel time can help crews plan when ground control can reply.",
                    {"power": 2.0},
                ),
                _decision(
                    "communication_autonomous",
                    "Use a pre-approved autonomous procedure",
                    "No resource cost",
                    "No resource change; earns 3 practice Science points.",
                    "Pre-approved procedures help crews act safely when Earth cannot respond immediately.",
                ),
                _decision(
                    "communication_schedule",
                    "Schedule a non-urgent communication session",
                    "Costs 1 simulated Power unit",
                    "Uses 1 simulated Power and earns 1 practice Science point.",
                    "Scheduling non-urgent messages around light time supports realistic mission planning.",
                    {"power": 1.0},
                ),
            ],
            day_triggered=day,
        ),
    ]
    return training_events, seen_event_ids
