"""Validate a bounded STEREO-A IMPACT HET daily ASCII product."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "space_weather" / "stereo_impact"
REPORT_PATH = ROOT / "datasets" / "validation_reports" / "stereo_impact_validation.json"

DATA_FILE = "AeH12Mar.1d"
SPDF_README = "00readme_ascii_sta_impact_het"
INSTRUMENT_DOC = "HET_public.html"
EXPECTED_DATA_SIZE = 10_532
EXPECTED_README_SIZE = 1_444
DATA_URL = (
    "https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/"
    "impact_ascii/het/1day/AeH12Mar.1d"
)
README_URL = (
    "https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/"
    "impact_ascii/het/00readme_ascii_sta_impact_het"
)
INSTRUMENT_DOC_URL = "https://izw1.caltech.edu/STEREO/Level1/HET_public.html"
EXPECTED_CHANNELS = (
    (0.7, 1.4, "e"),
    (1.4, 2.8, "e"),
    (2.8, 4.0, "e"),
    (13.6, 15.1, "H"),
    (14.9, 17.1, "H"),
    (17.0, 19.3, "H"),
    (20.8, 23.8, "H"),
    (23.8, 26.4, "H"),
    (26.3, 29.7, "H"),
    (29.5, 33.4, "H"),
    (33.4, 35.8, "H"),
    (35.5, 40.5, "H"),
    (40.0, 60.0, "H"),
    (60.0, 100.0, "H"),
)
CHANNEL_PATTERN = re.compile(
    r"F2\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+([eH])\Z"
)


class TextExtractor(HTMLParser):
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


def parse_header_date(line: str) -> datetime:
    return datetime.strptime(" ".join(line.split()), "%Y %b %d %H%M")


def channel_name(energy_min: float, energy_max: float, species: str) -> str:
    particle = "electron" if species == "e" else "proton"
    return f"{particle}_{energy_min:g}_{energy_max:g}_MeV"


def extract_html_text(path: Path) -> str:
    parser = TextExtractor()
    parser.feed(path.read_text(encoding="utf-8"))
    return " ".join(" ".join(parser.parts).split())


def validate() -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat()
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}
    files: dict[str, Any] = {}
    result: dict[str, Any] = {
        "checked_at_utc": checked_at,
        "dataset_name": "STEREO-A IMPACT HET daily electron/proton intensities",
        "dataset_id": "STEREO-A/IMPACT/HET/AeH12Mar.1d",
        "spacecraft": "STEREO-A (Ahead)",
        "instrument": "IMPACT High Energy Telescope (HET)",
        "product": "Level 2 1-day averaged ASCII list file",
        "source_urls": {
            "data": DATA_URL,
            "SPDF_readme": README_URL,
            "instrument_documentation": INSTRUMENT_DOC_URL,
            "STEREO_A_archive": "https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/",
            "STEREO_B_archive": "https://spdf.gsfc.nasa.gov/pub/data/stereo/behind/",
        },
        "raw_directory": str(RAW_DIR),
        "files": files,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }

    required_files = (DATA_FILE, SPDF_README, INSTRUMENT_DOC)
    for name in required_files:
        path = RAW_DIR / name
        exists = path.is_file()
        checks[f"{name}_exists"] = exists
        if not exists:
            errors.append(f"Required source or documentation file is missing: {name}")
            continue
        files[name] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "official_url": {
                DATA_FILE: DATA_URL,
                SPDF_README: README_URL,
                INSTRUMENT_DOC: INSTRUMENT_DOC_URL,
            }[name],
        }

    if DATA_FILE in files:
        checks["data_size_matches_official_content_length"] = (
            files[DATA_FILE]["size_bytes"] == EXPECTED_DATA_SIZE
        )
        if not checks["data_size_matches_official_content_length"]:
            errors.append(
                f"The data file has {files[DATA_FILE]['size_bytes']} bytes; "
                f"SPDF reported {EXPECTED_DATA_SIZE} bytes before download."
            )
    if SPDF_README in files:
        checks["SPDF_readme_size_matches_content_length"] = (
            files[SPDF_README]["size_bytes"] == EXPECTED_README_SIZE
        )
        if not checks["SPDF_readme_size_matches_content_length"]:
            errors.append("The SPDF README size does not match its reported length.")

    if errors:
        result["status"] = "FAILED"
        _write_report(result)
        return result

    readme_text = (RAW_DIR / SPDF_README).read_text(encoding="utf-8")
    checks["SPDF_readme_identifies_IMPACT_HET"] = (
        "STEREO IMPACT HET fluxes" in readme_text
    )
    checks["SPDF_readme_links_Ahead_HET_source"] = (
        "STEREO/DATA/HET/ahead/" in readme_text
    )
    if not checks["SPDF_readme_identifies_IMPACT_HET"]:
        errors.append("The retained SPDF README does not identify the HET product.")

    try:
        documentation = extract_html_text(RAW_DIR / INSTRUMENT_DOC)
        lowered_documentation = documentation.lower()
        required_documentation = {
            "instrument describes daily averages": "daily averaged electron and proton intensities"
            in lowered_documentation,
            "documented flux units are present": "particles/(cm2-sr-sec-mev)"
            in lowered_documentation,
            "documented lack of electron calibration": "calibration of the het electron channels is not currently correct"
            in lowered_documentation,
            "background caveat is present": "do not have any background corrections applied"
            in lowered_documentation,
            "unfilled data gaps are documented": "data gaps in these het files are not filled"
            in lowered_documentation,
        }
        checks.update(
            {f"instrument_doc_{key}": value for key, value in required_documentation.items()}
        )
        for description, present in required_documentation.items():
            if not present:
                errors.append(f"The official HET documentation is missing: {description}.")
    except (OSError, UnicodeError) as exc:
        errors.append(f"Could not read the official HET documentation: {exc}")

    data_report: dict[str, Any] = {}
    try:
        source_bytes = (RAW_DIR / DATA_FILE).read_bytes()
        text = source_bytes.decode("ascii")
        lines = text.splitlines()
        marker_index = next(
            (index for index, line in enumerate(lines) if line.strip() == "#End"),
            None,
        )
        checks["ASCII_decode_succeeded"] = True
        checks["HET_header_terminator_present"] = marker_index is not None
        if marker_index is None:
            raise ValueError("The required #End header terminator is missing.")
        if len(lines) < 7 or lines[0].strip() != "ASCII" or lines[1].strip() != "List file":
            raise ValueError("The file does not have the documented ASCII List header.")
        checks["ASCII_List_header_present"] = True

        declared_start = parse_header_date(lines[2])
        declared_end = parse_header_date(lines[3])
        t2_lines = [line.strip() for line in lines[5:marker_index] if line.strip().startswith("T2")]
        checks["header_declares_start_end_time_T2"] = len(t2_lines) == 1
        if len(t2_lines) != 1:
            errors.append("The HET header is missing its single T2 start/end time declaration.")
        channel_definitions: list[dict[str, Any]] = []
        for line in lines[5:marker_index]:
            match = CHANNEL_PATTERN.fullmatch(line.strip())
            if match is None:
                continue
            lower_bound, upper_bound, energy_min, energy_max = (
                float(match.group(index)) for index in range(1, 5)
            )
            species = match.group(5)
            channel_definitions.append(
                {
                    "name": channel_name(energy_min, energy_max, species),
                    "species_code": species,
                    "particle": "electron" if species == "e" else "proton",
                    "energy_min_MeV": energy_min,
                    "energy_max_MeV": energy_max,
                    "header_value_min": lower_bound,
                    "header_value_max": upper_bound,
                    "intensity_column_1_based": 10 + 2 * len(channel_definitions),
                    "uncertainty_column_1_based": 11 + 2 * len(channel_definitions),
                    "intensity_units": "particles/(cm^2-sr-s-MeV)",
                    "uncertainty_units": "particles/(cm^2-sr-s-MeV)",
                    "uncertainty_description": "1-sigma uncertainty",
                }
            )

        checks["channel_count_is_14"] = len(channel_definitions) == len(EXPECTED_CHANNELS)
        expected_channel_values = [
            (
                channel["energy_min_MeV"],
                channel["energy_max_MeV"],
                channel["species_code"],
            )
            for channel in channel_definitions
        ]
        checks["channel_definitions_match_official_documentation"] = (
            len(expected_channel_values) == len(EXPECTED_CHANNELS)
            and all(
                observed == expected
                for observed, expected in zip(expected_channel_values, EXPECTED_CHANNELS)
            )
        )
        if not checks["channel_count_is_14"]:
            errors.append(
                f"The HET header declares {len(channel_definitions)} channels; expected 14."
            )
        if not checks["channel_definitions_match_official_documentation"]:
            errors.append("HET channel energies or particle species do not match the official guide.")
        if any(
            channel["header_value_min"] > channel["header_value_max"]
            or channel["energy_min_MeV"] >= channel["energy_max_MeV"]
            for channel in channel_definitions
        ):
            errors.append("The HET header contains invalid channel energy or value bounds.")

        data_lines = [
            (line_number, line)
            for line_number, line in enumerate(lines[marker_index + 1 :], marker_index + 2)
            if line.strip() and not line.lstrip().startswith(";")
        ]
        rows: list[dict[str, Any]] = []
        malformed_rows: list[dict[str, Any]] = []
        for line_number, line in data_lines:
            fields = line.split()
            if len(fields) != 9 + 2 * len(channel_definitions):
                malformed_rows.append(
                    {
                        "line": line_number,
                        "field_count": len(fields),
                        "expected_field_count": 9 + 2 * len(channel_definitions),
                    }
                )
                continue
            try:
                if fields[0] != "0":
                    raise ValueError(f"Unexpected verse number: {fields[0]}")
                start = parse_header_date(" ".join(fields[1:5]))
                end = parse_header_date(" ".join(fields[5:9]))
                values = [float(field) for field in fields[9:]]
            except ValueError as exc:
                malformed_rows.append({"line": line_number, "error": str(exc)})
                continue
            rows.append(
                {
                    "line": line_number,
                    "start": start,
                    "end": end,
                    "values": values,
                }
            )

        if malformed_rows:
            errors.append(
                f"{len(malformed_rows)} data lines do not match the documented "
                "HET record structure."
            )
        checks["all_data_lines_have_documented_width_and_types"] = not malformed_rows
        checks["data_rows_present"] = bool(rows)
        if not rows:
            errors.append("No HET measurement records were found after #End.")

        ordered = all(
            rows[index]["start"] < rows[index + 1]["start"]
            for index in range(len(rows) - 1)
        )
        checks["record_start_times_are_strictly_increasing"] = ordered
        if not ordered:
            errors.append("HET record start timestamps are not strictly increasing.")

        valid_intervals = all(
            row["start"] < row["end"]
            and row["start"] == declared_start + timedelta(days=index)
            and row["end"] == row["start"] + timedelta(days=1)
            for index, row in enumerate(rows)
        )
        checks["records_are_contiguous_daily_intervals"] = valid_intervals
        expected_record_count = (declared_end - declared_start).days
        checks["daily_record_count_matches_header_interval"] = (
            len(rows) == expected_record_count
        )
        if not valid_intervals or len(rows) != expected_record_count:
            warnings.append(
                "One or more daily intervals are missing or inconsistent with the "
                "header coverage. The official HET guide states that data gaps are "
                "not filled in these files."
            )
        checks["first_and_last_record_match_header_coverage"] = bool(
            rows
            and rows[0]["start"] == declared_start
            and rows[-1]["end"] == declared_end
        )
        if not checks["first_and_last_record_match_header_coverage"]:
            errors.append("The first/last record does not span the header coverage.")

        channel_summaries: list[dict[str, Any]] = []
        nonfinite_count = 0
        out_of_header_range: dict[str, int] = {}
        for channel_index, channel in enumerate(channel_definitions):
            flux_values: list[float] = []
            uncertainty_values: list[float] = []
            out_of_range_count = 0
            for row in rows:
                flux = row["values"][2 * channel_index]
                uncertainty = row["values"][2 * channel_index + 1]
                for value in (flux, uncertainty):
                    if not math.isfinite(value):
                        nonfinite_count += 1
                    elif value < channel["header_value_min"] or value > channel["header_value_max"]:
                        out_of_range_count += 1
                if math.isfinite(flux):
                    flux_values.append(flux)
                if math.isfinite(uncertainty):
                    uncertainty_values.append(uncertainty)
            if out_of_range_count:
                out_of_header_range[channel["name"]] = out_of_range_count
            channel_summaries.append(
                {
                    **channel,
                    "intensity_record_count": len(flux_values),
                    "uncertainty_record_count": len(uncertainty_values),
                    "intensity_missing_or_nonfinite_count": len(rows) - len(flux_values),
                    "uncertainty_missing_or_nonfinite_count": len(rows)
                    - len(uncertainty_values),
                    "observed_intensity_min": min(flux_values) if flux_values else None,
                    "observed_intensity_max": max(flux_values) if flux_values else None,
                    "observed_uncertainty_min": min(uncertainty_values)
                    if uncertainty_values
                    else None,
                    "observed_uncertainty_max": max(uncertainty_values)
                    if uncertainty_values
                    else None,
                    "values_outside_F2_header_range": out_of_range_count,
                }
            )

        checks["all_observed_values_are_finite"] = nonfinite_count == 0
        if nonfinite_count:
            warnings.append(
                f"{nonfinite_count} numeric positions contain non-finite values. "
                "No values were replaced."
            )
        checks["values_within_F2_header_value_ranges"] = not out_of_header_range
        if out_of_header_range:
            warnings.append(
                "Values outside the per-channel F2 bounds declared in the file "
                f"header: {out_of_header_range}. Raw values were retained."
            )

        row_gaps = [
            (rows[index]["end"], rows[index + 1]["start"])
            for index in range(len(rows) - 1)
            if rows[index]["end"] != rows[index + 1]["start"]
        ]
        data_report = {
            "format": "ASCII List file (SPDF IMPACT HET documented format)",
            "file_size_bytes": len(source_bytes),
            "sha256": hashlib.sha256(source_bytes).hexdigest().upper(),
            "header_coverage_utc": {
                "start": declared_start.isoformat() + "Z",
                "end": declared_end.isoformat() + "Z",
            },
            "observed_record_coverage_utc": (
                {
                    "start": rows[0]["start"].isoformat() + "Z",
                    "end": rows[-1]["end"].isoformat() + "Z",
                }
                if rows
                else None
            ),
            "time_resolution": "1 day",
            "record_count": len(rows),
            "expected_daily_record_count": expected_record_count,
            "record_intervals_are_24_hours": valid_intervals,
            "inter_record_gaps": [
                {"after_utc": start.isoformat() + "Z", "before_utc": end.isoformat() + "Z"}
                for start, end in row_gaps
            ],
            "missing_value_convention": (
                "The downloaded HET guide specifies that data gaps are not filled; "
                "it does not define a numeric fill sentinel for this ASCII product. "
                "No sentinel was assumed."
            ),
            "documented_value_bounds": (
                "Each F2 channel header declares lower/upper values; validator "
                "compares measurements and 1-sigma uncertainties to those header "
                "bounds without modifying the source."
            ),
            "measurement_and_uncertainty_channel_count": len(channel_definitions),
            "nonfinite_numeric_values": nonfinite_count,
            "values_outside_header_bounds": out_of_header_range,
            "channels": channel_summaries,
            "malformed_rows": malformed_rows,
        }
    except (OSError, UnicodeError, ValueError, IndexError, OverflowError) as exc:
        errors.append(f"Could not parse or validate the STEREO HET ASCII file: {exc}")

    result["data"] = data_report
    result["status"] = "FAILED" if errors else (
        "PASSED_WITH_WARNINGS" if warnings else "PASS"
    )
    _write_report(result)
    return result


def _write_report(result: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    report = validate()
    print(
        f"STEREO IMPACT validation: {report['status']}; "
        f"errors={len(report['errors'])}; warnings={len(report['warnings'])}"
    )
    print(f"Report: {REPORT_PATH}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    raise SystemExit(1 if report["errors"] else 0)
