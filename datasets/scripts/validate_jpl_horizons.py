"""Validate the bounded Earth-Moon Horizons observer-table response."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "communication_navigation" / "jpl_horizons"
REPORT_PATH = ROOT / "datasets" / "validation_reports" / "jpl_horizons_validation.json"
RESPONSE_FILE = "horizons_response.json"
METADATA_FILE = "request_metadata.json"
API_DOC_FILE = "horizons_api_documentation.html"
MANUAL_FILE = "horizons_manual.html"
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
RECORD_PATTERN = re.compile(
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


def html_text(path: Path) -> str:
    parser = HTMLTextExtractor()
    parser.feed(path.read_text(encoding="utf-8"))
    return " ".join(" ".join(parser.parts).split())


def write_report(result: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate() -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat()
    checks: dict[str, bool] = {}
    errors: list[str] = []
    warnings: list[str] = []
    files: dict[str, Any] = {}
    result: dict[str, Any] = {
        "checked_at_utc": checked_at,
        "dataset_name": "JPL Horizons Moon geocentric range and down-leg light time",
        "dataset_id": "Horizons target 301, observer 500@399, DE441",
        "source_urls": {
            "api": ENDPOINT,
            "api_documentation": "https://ssd-api.jpl.nasa.gov/doc/horizons.html",
            "horizons_manual": "https://ssd.jpl.nasa.gov/horizons/manual.html",
        },
        "raw_directory": str(RAW_DIR),
        "files": files,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }

    required_files = (RESPONSE_FILE, METADATA_FILE, API_DOC_FILE, MANUAL_FILE)
    for filename in required_files:
        path = RAW_DIR / filename
        exists = path.is_file()
        checks[f"{filename}_exists"] = exists
        if not exists:
            errors.append(f"Required response, metadata or documentation file is missing: {filename}")
            continue
        size = path.stat().st_size
        checks[f"{filename}_nonempty"] = size > 0
        if size == 0:
            errors.append(f"Required file is empty: {filename}")
        files[filename] = {
            "size_bytes": size,
            "sha256": sha256_file(path),
        }

    metadata: dict[str, Any] | None = None
    if METADATA_FILE in files:
        try:
            metadata = json.loads((RAW_DIR / METADATA_FILE).read_text(encoding="utf-8"))
            params = metadata.get("request_parameters")
            checks["request_parameters_match_expected"] = params == EXPECTED_PARAMETERS
            if params != EXPECTED_PARAMETERS:
                errors.append("Saved request parameters do not match the documented bounded query.")
            expected_url = ENDPOINT + "?" + urlencode(params or {})
            checks["request_url_matches_parameters"] = metadata.get("request_url") == expected_url
            checks["request_source_is_official_endpoint"] = metadata.get("source") == ENDPOINT
            if metadata.get("request_url") != expected_url or metadata.get("source") != ENDPOINT:
                errors.append("Saved request URL or source endpoint is inconsistent with its parameters.")
            retrieval_time = datetime.fromisoformat(metadata["retrieved_at_utc"])
            checks["retrieval_timestamp_is_utc"] = (
                retrieval_time.tzinfo is not None
                and retrieval_time.utcoffset() == timedelta(0)
            )
            if not checks["retrieval_timestamp_is_utc"]:
                errors.append("Retrieval timestamp is missing an explicit UTC timezone.")
            checks["http_status_successful"] = metadata.get("http_status") == 200
            if metadata.get("http_status") != 200:
                errors.append(f"Recorded HTTP status is not successful: {metadata.get('http_status')}")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            errors.append(f"Could not validate request metadata: {exc}")

    response_body: dict[str, Any] | None = None
    if RESPONSE_FILE in files:
        response_path = RAW_DIR / RESPONSE_FILE
        response_bytes = response_path.read_bytes()
        if metadata is not None:
            checks["response_file_matches_metadata_name"] = (
                metadata.get("response_file") == RESPONSE_FILE
            )
            checks["response_size_matches_metadata"] = (
                metadata.get("response_size_bytes") == len(response_bytes)
            )
            checks["response_sha256_matches_metadata"] = (
                metadata.get("response_sha256") == hashlib.sha256(response_bytes).hexdigest().upper()
            )
            if not all(
                checks[name]
                for name in (
                    "response_file_matches_metadata_name",
                    "response_size_matches_metadata",
                    "response_sha256_matches_metadata",
                )
            ):
                errors.append("Saved response integrity metadata does not match the original response file.")
        try:
            response_body = json.loads(response_bytes)
            checks["response_is_valid_json"] = isinstance(response_body, dict)
            checks["api_error_absent"] = (
                isinstance(response_body, dict) and "error" not in response_body
            )
            checks["api_signature_identifies_horizons"] = (
                isinstance(response_body, dict)
                and response_body.get("signature", {}).get("source") == "NASA/JPL Horizons API"
            )
            if not checks["response_is_valid_json"] or not checks["api_error_absent"]:
                errors.append("Horizons response JSON is invalid or contains an API error.")
            if not checks["api_signature_identifies_horizons"]:
                errors.append("Response signature does not identify NASA/JPL Horizons.")
        except (json.JSONDecodeError, AttributeError, TypeError) as exc:
            errors.append(f"Could not parse the Horizons JSON response: {exc}")

    if API_DOC_FILE in files and MANUAL_FILE in files:
        try:
            api_doc = html_text(RAW_DIR / API_DOC_FILE)
            manual = html_text(RAW_DIR / MANUAL_FILE)
            checks["official_api_doc_describes_quantities_and_range_units"] = (
                "QUANTITIES" in api_doc and "RANGE_UNITS" in api_doc
            )
            checks["manual_documents_geocenter_code_500"] = (
                "500 is the geocenter" in manual
            )
            checks["manual_documents_range_units"] = (
                "Target apparent range" in manual and "Units: {AU,KM}" in manual
            )
            checks["manual_documents_down_leg_light_time_minutes"] = (
                "Target one-way down-leg light-time" in manual
                and "Units: MINUTES" in manual
            )
            for name, passed in checks.items():
                if name.startswith(("official_api_doc_", "manual_")) and not passed:
                    errors.append(f"Official documentation does not support required field: {name}")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Could not read the retained official documentation: {exc}")

    parsed_rows: list[dict[str, Any]] = []
    response_text = response_body.get("result") if isinstance(response_body, dict) else None
    if isinstance(response_text, str):
        checks["target_is_moon_301"] = "Target body name: Moon (301)" in response_text
        checks["center_is_earth_399"] = "Center body name: Earth (399)" in response_text
        checks["center_site_is_geocentric"] = "Center-site name: GEOCENTRIC" in response_text
        checks["ephemeris_source_is_de441"] = "{source: DE441}" in response_text
        checks["response_time_range_matches_request"] = (
            "Start time      : A.D. 2026-Nov-14 00:00:00.0000 UT" in response_text
            and "Stop  time      : A.D. 2026-Nov-21 00:00:00.0000 UT" in response_text
        )
        header = next(
            (line for line in response_text.splitlines() if "Date__(UT)__HR:MN:SS" in line),
            "",
        )
        checks["response_has_expected_quantity_columns"] = all(
            label in header
            for label in ("delta", "deldot", "1-way_down_LT")
        )
        if not all(
            checks[name]
            for name in (
                "target_is_moon_301",
                "center_is_earth_399",
                "center_site_is_geocentric",
                "ephemeris_source_is_de441",
                "response_time_range_matches_request",
                "response_has_expected_quantity_columns",
            )
        ):
            errors.append("Horizons response target, observer, time range, source or columns are inconsistent.")

        start_marker = response_text.find("$$SOE")
        end_marker = response_text.find("$$EOE")
        checks["ephemeris_table_markers_present"] = (
            start_marker >= 0 and end_marker > start_marker
        )
        if not checks["ephemeris_table_markers_present"]:
            errors.append("Horizons response is missing its ephemeris table markers.")
        else:
            for line in response_text[start_marker + len("$$SOE"):end_marker].splitlines():
                if not line.strip():
                    continue
                match = RECORD_PATTERN.match(line)
                if match is None:
                    errors.append(f"Could not parse an ephemeris row: {line.strip()}")
                    continue
                try:
                    timestamp = datetime.strptime(
                        f"{match.group(1)} {match.group(2)}", "%Y-%b-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc)
                    delta_km, deldot_km_s, light_time_min = (
                        float(match.group(index)) for index in (3, 4, 5)
                    )
                    parsed_rows.append({
                        "timestamp_utc": timestamp,
                        "delta_km": delta_km,
                        "deldot_km_s": deldot_km_s,
                        "one_way_down_light_time_minutes": light_time_min,
                    })
                except (ValueError, OverflowError) as exc:
                    errors.append(f"Invalid ephemeris value or timestamp in row: {line.strip()} ({exc})")

    if metadata is not None and isinstance(metadata.get("request_parameters"), dict):
        params = metadata["request_parameters"]
        try:
            start = datetime.strptime(params["START_TIME"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            stop = datetime.strptime(params["STOP_TIME"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            expected_count = (stop - start).days + 1
            checks["daily_sample_count_matches_requested_interval"] = len(parsed_rows) == expected_count
            checks["first_and_last_samples_match_requested_dates"] = bool(parsed_rows) and (
                parsed_rows[0]["timestamp_utc"] == start
                and parsed_rows[-1]["timestamp_utc"] == stop
            )
            checks["timestamps_are_strictly_ordered"] = all(
                parsed_rows[index]["timestamp_utc"] < parsed_rows[index + 1]["timestamp_utc"]
                for index in range(len(parsed_rows) - 1)
            )
            checks["sampling_is_daily_utc"] = all(
                parsed_rows[index + 1]["timestamp_utc"] - parsed_rows[index]["timestamp_utc"]
                == timedelta(days=1)
                for index in range(len(parsed_rows) - 1)
            ) and all(row["timestamp_utc"].hour == 0 for row in parsed_rows)
            checks["distance_and_light_time_are_finite_and_positive"] = all(
                math.isfinite(row["delta_km"])
                and row["delta_km"] > 0
                and math.isfinite(row["one_way_down_light_time_minutes"])
                and row["one_way_down_light_time_minutes"] > 0
                for row in parsed_rows
            )
            checks["range_rate_is_finite"] = all(
                math.isfinite(row["deldot_km_s"]) for row in parsed_rows
            )
            required_checks = (
                "daily_sample_count_matches_requested_interval",
                "first_and_last_samples_match_requested_dates",
                "timestamps_are_strictly_ordered",
                "sampling_is_daily_utc",
                "distance_and_light_time_are_finite_and_positive",
                "range_rate_is_finite",
            )
            if not all(checks[name] for name in required_checks):
                errors.append("Ephemeris rows contain missing, invalid, unordered or non-daily values.")
            result["request_parameters"] = params
            result["time_coverage_utc"] = {
                "start": params["START_TIME"],
                "end": params["STOP_TIME"],
                "sample_count": len(parsed_rows),
            }
            if metadata is not None:
                retrieval_time = datetime.fromisoformat(metadata["retrieved_at_utc"])
                future_count = sum(
                    row["timestamp_utc"] > retrieval_time for row in parsed_rows
                )
                if future_count:
                    warning = (
                        f"{future_count} requested epoch(s) are after retrieval time; "
                        "these are forward ephemeris calculations, not observations."
                    )
                    warnings.append(warning)
                    result["temporal_interpretation"] = warning
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"Could not validate sample coverage against request parameters: {exc}")

    if parsed_rows:
        result["variables"] = {
            "delta": {"meaning": "Target apparent range", "units": "km"},
            "deldot": {"meaning": "Target range rate; positive means receding", "units": "km/s"},
            "1-way_down_LT": {
                "meaning": "Target one-way down-leg light time as seen by observer",
                "units": "minutes",
            },
            "timestamp": {"meaning": "Ephemeris epoch", "units": "UTC"},
        }
        result["sample_values"] = {
            "first": {
                key: (value.isoformat() if isinstance(value, datetime) else value)
                for key, value in parsed_rows[0].items()
            },
            "last": {
                key: (value.isoformat() if isinstance(value, datetime) else value)
                for key, value in parsed_rows[-1].items()
            },
        }

    result["status"] = "FAILED" if errors else (
        "PASSED_WITH_WARNINGS" if warnings else "PASS"
    )
    write_report(result)
    return result


if __name__ == "__main__":
    report = validate()
    print(
        f"JPL Horizons validation: {report['status']}; "
        f"errors={len(report['errors'])}; warnings={len(report['warnings'])}"
    )
    print(f"Report: {REPORT_PATH}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    raise SystemExit(1 if report["errors"] else 0)
