"""Normalize the saved NASA/JPL Horizons Earth-Moon ephemeris response."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import tempfile
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "communication_navigation" / "jpl_horizons"
OUTPUT_DIR = ROOT / "datasets" / "processed" / "communication_navigation" / "jpl_horizons"
RESPONSE_FILE = "horizons_response.json"
REQUEST_FILE = "request_metadata.json"
API_DOC_FILE = "horizons_api_documentation.html"
MANUAL_FILE = "horizons_manual.html"
VALIDATION_FILE = ROOT / "datasets" / "validation_reports" / "jpl_horizons_validation.json"
CSV_FILE = "jpl_horizons_moon_earth_geocenter_20261114_20261121.csv"
METADATA_FILE = "jpl_horizons_processing_metadata.json"
SUMMARY_FILE = "jpl_horizons_summary_statistics.json"
SCRIPT_VERSION = "1.0.0"
ENDPOINT = "https://ssd.jpl.nasa.gov/api/horizons.api"
EXPECTED_PARAMETERS = {
    "format": "json",
    "COMMAND": "301",
    "OBJ_DATA": "YES",
    "MAKE_EPHEM": "YES",
    "EPHEM_TYPE": "OBSERVER",
    "CENTER": "500@399",
    "START_TIME": "2026-11-14",
    "STOP_TIME": "2026-11-21",
    "STEP_SIZE": "1d",
    "TIME_TYPE": "UT",
    "TIME_ZONE": "+00:00",
    "QUANTITIES": "20,21",
    "RANGE_UNITS": "KM",
    "TIME_DIGITS": "SECONDS",
}
ROW_PATTERN = re.compile(
    r"^\s*(\d{4}-[A-Za-z]{3}-\d{2})\s+(\d{2}:\d{2}:\d{2})"
    r"\s+(\S+)\s+(\S+)\s+(\S+)\s*$"
)


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _html_text(path: Path) -> str:
    parser = HTMLTextExtractor()
    parser.feed(path.read_text(encoding="utf-8"))
    return " ".join(" ".join(parser.parts).split())


def _decimal(token: str, label: str) -> Decimal:
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid {label} value in Horizons output: {token!r}.") from exc
    if not value.is_finite():
        raise ValueError(f"Non-finite {label} value in Horizons output: {token!r}.")
    return value


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _utc_datetime(date_token: str, time_token: str) -> datetime:
    parsed = datetime.strptime(f"{date_token} {time_token}", "%Y-%b-%d %H:%M:%S")
    return parsed.replace(tzinfo=timezone.utc)


def _decimal_stats(values: list[Decimal]) -> dict[str, str | int]:
    if not values:
        raise ValueError("Cannot calculate statistics for an empty ephemeris column.")
    ordered = sorted(values)
    with localcontext() as context:
        context.prec = 40
        mean = sum(values, Decimal(0)) / Decimal(len(values))
    median = statistics.median(ordered)
    return {
        "minimum": _decimal_text(ordered[0]),
        "maximum": _decimal_text(ordered[-1]),
        "mean": _decimal_text(mean),
        "median": _decimal_text(median),
        "valid_value_count": len(values),
        "missing_or_invalid_value_count": 0,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _parse() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    response_path = RAW_DIR / RESPONSE_FILE
    request_path = RAW_DIR / REQUEST_FILE
    response_bytes = response_path.read_bytes()
    response = json.loads(response_bytes)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION_FILE.read_text(encoding="utf-8"))

    if response.get("error") is not None:
        raise ValueError(f"Horizons response reports an API error: {response['error']}")
    if response.get("signature", {}).get("source") != "NASA/JPL Horizons API":
        raise ValueError("Response signature does not identify the NASA/JPL Horizons API.")
    params = request.get("request_parameters")
    if params != EXPECTED_PARAMETERS:
        raise ValueError("Saved request parameters do not match the retained Horizons query.")
    if request.get("source") != ENDPOINT:
        raise ValueError("Saved request source is not the official Horizons API endpoint.")
    if request.get("request_url") != ENDPOINT + "?" + urlencode(params):
        raise ValueError("Saved request URL does not match the original request parameters.")
    if request.get("http_status") != 200 or request.get("response_file") != RESPONSE_FILE:
        raise ValueError("Saved request metadata does not indicate the expected successful response.")
    if request.get("response_size_bytes") != len(response_bytes):
        raise ValueError("Saved response size differs from request metadata.")
    source_sha256 = hashlib.sha256(response_bytes).hexdigest().upper()
    if request.get("response_sha256") != source_sha256:
        raise ValueError("Saved response SHA-256 differs from request metadata.")
    if validation.get("status") != "PASSED_WITH_WARNINGS" or validation.get("errors"):
        raise ValueError("Expected the existing Horizons validation report PASSED_WITH_WARNINGS.")
    if not validation.get("checks", {}).get("response_sha256_matches_metadata"):
        raise ValueError("Existing validation did not verify response integrity.")

    result_text = response.get("result")
    if not isinstance(result_text, str):
        raise ValueError("Horizons response has no ephemeris result text.")
    if "Target body name: Moon (301)" not in result_text:
        raise ValueError("Response target is not the Moon (NAIF ID 301).")
    if "Center body name: Earth (399)" not in result_text:
        raise ValueError("Response center is not Earth (399).")
    if "Center-site name: GEOCENTRIC" not in result_text:
        raise ValueError("Response observer site is not geocentric.")
    if "{source: DE441}" not in result_text:
        raise ValueError("Response does not identify DE441 as its ephemeris source.")

    lines = result_text.splitlines()
    table_header = next(
        (line for line in lines if "Date__(UT)__HR:MN:SS" in line),
        None,
    )
    if table_header is None or not all(
        label in table_header for label in ("delta", "deldot", "1-way_down_LT")
    ):
        raise ValueError("Horizons ephemeris table does not have the requested columns.")
    if "Units conversion:" not in result_text or "1 au= 149597870.700 km" not in result_text:
        raise ValueError("Expected Horizons response unit conversion metadata was not found.")

    api_doc = _html_text(RAW_DIR / API_DOC_FILE)
    manual = _html_text(RAW_DIR / MANUAL_FILE)
    if "RANGE_UNITS" not in api_doc or "20. Target range & range rate" not in manual:
        raise ValueError("Official Horizons documentation does not confirm the queried quantities.")
    if "Units are AU and KM/S" not in manual or "Units: MINUTES" not in manual:
        raise ValueError("Official Horizons manual units for range/rate/light time were not found.")
    if "Target one-way down-leg light-time" not in manual:
        raise ValueError("Official manual definition of down-leg light time was not found.")

    soe, eoe = result_text.find("$$SOE"), result_text.find("$$EOE")
    if soe < 0 or eoe <= soe:
        raise ValueError("Horizons result is missing its ephemeris table markers.")

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        result_text[soe + len("$$SOE") : eoe].splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        match = ROW_PATTERN.fullmatch(line)
        if match is None:
            raise ValueError(f"Cannot parse ephemeris row {line_number}: {line.strip()!r}.")
        date_token, time_token, range_token, rate_token, light_token = match.groups()
        epoch = _utc_datetime(date_token, time_token)
        range_km = _decimal(range_token, "range")
        range_rate_km_s = _decimal(rate_token, "range rate")
        one_way_minutes = _decimal(light_token, "one-way down-leg light time")
        if range_km <= 0 or one_way_minutes <= 0:
            raise ValueError(f"Range and light time must be positive at {_iso_utc(epoch)}.")
        with localcontext() as context:
            context.prec = 40
            two_way_seconds = one_way_minutes * Decimal(120)
        rows.append(
            {
                "epoch_utc": _iso_utc(epoch),
                "epoch": epoch,
                "range_km": range_km,
                "range_km_source_token": range_token,
                "range_rate_km_s": range_rate_km_s,
                "range_rate_km_s_source_token": rate_token,
                "one_way_down_leg_light_time_minutes": one_way_minutes,
                "one_way_down_leg_light_time_minutes_source_token": light_token,
                "two_way_vacuum_light_time_seconds": two_way_seconds,
            }
        )

    start = datetime.strptime(params["START_TIME"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    stop = datetime.strptime(params["STOP_TIME"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    expected_count = (stop - start).days + 1
    if len(rows) != expected_count or len(rows) != 8:
        raise ValueError(f"Expected eight daily epochs; found {len(rows)}.")
    for index, row in enumerate(rows):
        expected_epoch = start + timedelta(days=index)
        if row["epoch"] != expected_epoch:
            raise ValueError(f"Epoch {row['epoch_utc']} does not match the expected daily UTC schedule.")

    return rows, {
        "response": response,
        "request": request,
        "validation": validation,
        "source_sha256": source_sha256,
        "source_size_bytes": len(response_bytes),
        "table_header": table_header.strip(),
        "start": start,
        "stop": stop,
        "api_documentation": api_doc,
        "manual": manual,
    }


def process() -> dict[str, Any]:
    required = (
        RAW_DIR / RESPONSE_FILE,
        RAW_DIR / REQUEST_FILE,
        RAW_DIR / API_DOC_FILE,
        RAW_DIR / MANUAL_FILE,
        VALIDATION_FILE,
    )
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required Horizons source files are missing: {missing}.")
    raw_hashes_before = {
        path.name: sha256_file(path)
        for path in sorted(RAW_DIR.iterdir())
        if path.is_file()
    }
    rows, parsed = _parse()
    if raw_hashes_before[RESPONSE_FILE] != parsed["source_sha256"]:
        raise RuntimeError("The original Horizons response changed while processing.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / CSV_FILE
    metadata_path = OUTPUT_DIR / METADATA_FILE
    summary_path = OUTPUT_DIR / SUMMARY_FILE
    fieldnames = [
        "epoch_utc",
        "earth_moon_range_km",
        "range_rate_km_s",
        "one_way_down_leg_light_time_minutes",
        "two_way_vacuum_light_time_seconds_derived",
    ]

    fd, temporary_name = tempfile.mkstemp(prefix=CSV_FILE, suffix=".tmp", dir=OUTPUT_DIR)
    os.close(fd)
    temporary_csv = Path(temporary_name)
    try:
        with temporary_csv.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "epoch_utc": row["epoch_utc"],
                        "earth_moon_range_km": row["range_km_source_token"],
                        "range_rate_km_s": row["range_rate_km_s_source_token"],
                        "one_way_down_leg_light_time_minutes": (
                            row["one_way_down_leg_light_time_minutes_source_token"]
                        ),
                        "two_way_vacuum_light_time_seconds_derived": _decimal_text(
                            row["two_way_vacuum_light_time_seconds"]
                        ),
                    }
                )
        with temporary_csv.open("r", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            reopened = list(reader)
            if reader.fieldnames != fieldnames:
                raise ValueError("Reopened Horizons CSV has unexpected columns.")
        if len(reopened) != len(rows):
            raise ValueError("Reopened Horizons CSV row count differs from the original response.")
        for source_row, output_row in zip(rows, reopened):
            if output_row["epoch_utc"] != source_row["epoch_utc"]:
                raise ValueError("Reopened Horizons epoch does not match the response.")
            if output_row["earth_moon_range_km"] != source_row["range_km_source_token"]:
                raise ValueError("Reopened Horizons range differs from its original decimal token.")
            if output_row["range_rate_km_s"] != source_row["range_rate_km_s_source_token"]:
                raise ValueError("Reopened Horizons range rate differs from its original decimal token.")
            if output_row["one_way_down_leg_light_time_minutes"] != (
                source_row["one_way_down_leg_light_time_minutes_source_token"]
            ):
                raise ValueError("Reopened Horizons one-way light time differs from its source token.")
            expected_two_way = source_row["one_way_down_leg_light_time_minutes"] * Decimal(120)
            if Decimal(output_row["two_way_vacuum_light_time_seconds_derived"]) != expected_two_way:
                raise ValueError("Reopened derived two-way vacuum light time is inconsistent.")
        os.replace(temporary_csv, csv_path)
    finally:
        if temporary_csv.exists():
            temporary_csv.unlink()

    range_values = [row["range_km"] for row in rows]
    range_rates = [row["range_rate_km_s"] for row in rows]
    one_way_values = [row["one_way_down_leg_light_time_minutes"] for row in rows]
    two_way_values = [row["two_way_vacuum_light_time_seconds"] for row in rows]
    retrieval_time = datetime.fromisoformat(parsed["request"]["retrieved_at_utc"])
    if retrieval_time.tzinfo is None or retrieval_time.utcoffset() != timedelta(0):
        raise ValueError("Saved retrieval timestamp must have UTC timezone information.")
    future_epochs = [row["epoch_utc"] for row in rows if row["epoch"] > retrieval_time]

    summary = {
        "dataset_name": "JPL Horizons Moon geocentric range and down-leg light time",
        "dataset_id": "Horizons target 301, observer 500@399, DE441",
        "computation_type": "Computed ephemeris, not a direct observation.",
        "epoch_count": len(rows),
        "time_coverage_utc": {
            "start": rows[0]["epoch_utc"],
            "end": rows[-1]["epoch_utc"],
        },
        "future_ephemeris_epoch_count_at_retrieval": len(future_epochs),
        "future_ephemeris_epochs_utc": future_epochs,
        "earth_moon_range_km": _decimal_stats(range_values),
        "range_rate_km_s": {
            **_decimal_stats(range_rates),
            "positive_means": "target receding from observer",
            "negative_means": "target approaching observer",
        },
        "one_way_down_leg_light_time_minutes": _decimal_stats(one_way_values),
        "two_way_vacuum_light_time_seconds_derived": {
            **_decimal_stats(two_way_values),
            "derivation": "2 * Horizons one-way down-leg light time (minutes) * 60 seconds/minute",
            "status": "Mathematical derivation, not a separate direct Horizons measurement.",
        },
        "network_or_system_delays_included": False,
        "units": {
            "earth_moon_range": "km",
            "range_rate": "km/s",
            "one_way_down_leg_light_time": "minutes",
            "derived_two_way_vacuum_light_time": "seconds",
        },
        "scientific_limitations": [
            "Horizons values are computed ephemerides; epochs after retrieval are forward calculations, not observations.",
            "One-way down-leg light time is not the complete communication delay for every mission geometry.",
            "Two-way vacuum light time is derived mathematically from the reported one-way value, not separately measured or separately reported by Horizons.",
            "No network latency, routing, equipment, operations, or processing delays are included.",
            "This dataset is not a real-time communication measurement and is not connected to gameplay.",
        ],
    }
    source_hashes_after = {
        path.name: sha256_file(path)
        for path in sorted(RAW_DIR.iterdir())
        if path.is_file()
    }
    if raw_hashes_before != source_hashes_after:
        raise RuntimeError("One or more original Horizons raw files changed during processing.")

    metadata = {
        "dataset_name": summary["dataset_name"],
        "source": "NASA/JPL Horizons API",
        "source_urls": {
            "api": ENDPOINT,
            "api_documentation": "https://ssd-api.jpl.nasa.gov/doc/horizons.html",
            "horizons_manual": "https://ssd.jpl.nasa.gov/horizons/manual.html",
        },
        "source_response_file": RESPONSE_FILE,
        "source_response_size_bytes": parsed["source_size_bytes"],
        "source_response_sha256": parsed["source_sha256"],
        "source_files_sha256": raw_hashes_before,
        "source_files_sha256_unchanged": True,
        "request_parameters": parsed["request"]["request_parameters"],
        "request_url": parsed["request"]["request_url"],
        "retrieved_at_utc": parsed["request"]["retrieved_at_utc"],
        "http_status": parsed["request"]["http_status"],
        "target": {
            "name": "Moon",
            "naif_id": 301,
        },
        "observer": {
            "body": "Earth",
            "body_id": 399,
            "center_code": "500@399",
            "reference_center": "Earth geocenter",
            "site": "GEOCENTRIC",
        },
        "ephemeris_source": "DE441",
        "time": {
            "request_time_type": "UT",
            "request_time_zone": "+00:00",
            "response_epochs_timezone": "UTC",
            "start_utc": _iso_utc(parsed["start"]),
            "stop_utc": _iso_utc(parsed["stop"]),
            "step": "1 day",
            "epoch_count": len(rows),
            "response_table_header": parsed["table_header"],
        },
        "variables": {
            "earth_moon_range_km": {
                "source_label": "delta",
                "meaning": "Target apparent range, light-time aberrated, relative to observer.",
                "units": "km",
                "preservation": "Original Horizons decimal token preserved in CSV.",
            },
            "range_rate_km_s": {
                "source_label": "deldot",
                "meaning": "Range rate; positive means receding, negative means approaching.",
                "units": "km/s",
                "preservation": "Original Horizons decimal token preserved in CSV.",
            },
            "one_way_down_leg_light_time_minutes": {
                "source_label": "1-way_down_LT",
                "meaning": "One-way down-leg light time from target center to observer.",
                "units": "minutes",
                "preservation": "Original Horizons decimal token preserved in CSV.",
            },
            "two_way_vacuum_light_time_seconds_derived": {
                "meaning": "Twice the Horizons one-way down-leg light time, converted from minutes to seconds.",
                "units": "seconds",
                "derivation": "2 * one_way_down_leg_light_time_minutes * 60",
                "is_direct_horizons_measurement": False,
            },
        },
        "processing_script": "datasets/scripts/process_jpl_horizons.py",
        "processing_script_version": SCRIPT_VERSION,
        "processed_csv_file": CSV_FILE,
        "processed_csv_size_bytes": csv_path.stat().st_size,
        "processed_csv_sha256": sha256_file(csv_path),
        "numeric_precision_policy": (
            "Original Horizons numeric strings are written directly to CSV without float conversion. "
            "The derived two-way value is calculated from Decimal arithmetic."
        ),
        "processed_csv_reopened_and_verified": True,
        "source_validation_status": parsed["validation"]["status"],
        "source_validation_warnings_preserved": parsed["validation"].get("warnings", []),
    }
    _write_json(metadata_path, metadata)
    _write_json(summary_path, summary)
    return {"metadata": metadata, "summary": summary}


if __name__ == "__main__":
    result = process()
    summary = result["summary"]
    print(
        f"JPL Horizons processing complete: {summary['epoch_count']} epochs, "
        f"{summary['future_ephemeris_epoch_count_at_retrieval']} forward-calculation epochs."
    )
    for name in (CSV_FILE, METADATA_FILE, SUMMARY_FILE):
        path = OUTPUT_DIR / name
        print(f"{path}: {path.stat().st_size} bytes")
