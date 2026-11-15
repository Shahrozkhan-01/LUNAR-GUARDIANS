"""Process the bounded STEREO-A IMPACT HET daily ASCII sample."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import statistics
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "space_weather" / "stereo_impact"
OUTPUT_DIR = ROOT / "datasets" / "processed" / "space_weather" / "stereo_impact"
DATA_FILE = "AeH12Mar.1d"
README_FILE = "00readme_ascii_sta_impact_het"
DOCUMENTATION_FILE = "HET_public.html"
VALIDATION_REPORT = ROOT / "datasets" / "validation_reports" / "stereo_impact_validation.json"
OUTPUT_CSV = "stereo_impact_het_201203_daily.csv.gz"
METADATA_FILE = "stereo_impact_processing_metadata.json"
SUMMARY_FILE = "stereo_impact_summary_statistics.json"
SCRIPT_VERSION = "1.0.0"
UNITS = "particles/(cm^2-sr-sec-MeV)"
CHANNEL_PATTERN = re.compile(r"F2\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+([eH])\Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_utc_date(fields: list[str] | tuple[str, ...]) -> datetime:
    parsed = datetime.strptime(" ".join(fields), "%Y %b %d %H%M")
    return parsed.replace(tzinfo=timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def channel_name(energy_min: float, energy_max: float, species: str) -> str:
    particle = "electron" if species == "e" else "proton"
    return f"{particle}_{energy_min:g}_{energy_max:g}_MeV"


def _read_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data_path = RAW_DIR / DATA_FILE
    raw_bytes = data_path.read_bytes()
    text = raw_bytes.decode("ascii")
    lines = text.splitlines()
    if len(lines) < 8 or lines[0].strip() != "ASCII" or lines[1].strip() != "List file":
        raise ValueError("Source does not have the documented ASCII List header.")

    marker_indices = [i for i, line in enumerate(lines) if line.strip() == "#End"]
    if len(marker_indices) != 1:
        raise ValueError(f"Expected one #End header marker; found {len(marker_indices)}.")
    marker_index = marker_indices[0]
    header_start = parse_utc_date(lines[2].split())
    header_end = parse_utc_date(lines[3].split())
    if header_start >= header_end:
        raise ValueError("Header coverage start must precede its end.")

    t2_lines = [line.strip() for line in lines[5:marker_index] if line.strip().startswith("T2")]
    if len(t2_lines) != 1 or t2_lines[0].split()[0] != "T2":
        raise ValueError("Expected exactly one T2 start/end time declaration.")

    verse_lines = [line.strip() for line in lines[5:marker_index] if line.strip().startswith("#")]
    if verse_lines != ["#0 Rate"]:
        raise ValueError(f"Unexpected verse declaration(s): {verse_lines!r}.")

    channels: list[dict[str, Any]] = []
    for line in lines[5:marker_index]:
        match = CHANNEL_PATTERN.fullmatch(line.strip())
        if match is None:
            continue
        value_min, value_max, energy_min, energy_max = (
            float(match.group(index)) for index in range(1, 5)
        )
        species_code = match.group(5)
        if value_min > value_max or energy_min >= energy_max:
            raise ValueError(f"Invalid F2 bounds in header: {line!r}.")
        channels.append(
            {
                "name": channel_name(energy_min, energy_max, species_code),
                "particle": "electron" if species_code == "e" else "proton",
                "species_code": species_code,
                "energy_min_MeV": energy_min,
                "energy_max_MeV": energy_max,
                "intensity_field": f"intensity_{channel_name(energy_min, energy_max, species_code)}",
                "uncertainty_field": f"uncertainty_{channel_name(energy_min, energy_max, species_code)}",
                "intensity_units": UNITS,
                "uncertainty_units": UNITS,
                "uncertainty_description": "1-sigma uncertainty",
                "header_value_min": value_min,
                "header_value_max": value_max,
                "intensity_column_1_based": 10 + 2 * len(channels),
                "uncertainty_column_1_based": 11 + 2 * len(channels),
                "source_header_line": line.strip(),
            }
        )
    if len(channels) != 14:
        raise ValueError(f"Expected 14 F2 channel definitions; found {len(channels)}.")

    validation = json.loads(VALIDATION_REPORT.read_text(encoding="utf-8"))
    if validation.get("status") != "PASS" or validation.get("errors") or validation.get("warnings"):
        raise ValueError("The existing STEREO raw validation report is not an unqualified PASS.")
    if not validation.get("checks", {}).get("channel_definitions_match_official_documentation"):
        raise ValueError("Existing validation did not confirm channels against official HET documentation.")
    validated_channels = validation.get("data", {}).get("channels", [])
    if len(validated_channels) != len(channels):
        raise ValueError("Validated report channel definitions do not match the HET file header.")
    for actual, expected in zip(channels, validated_channels):
        for key in ("name", "particle", "species_code", "energy_min_MeV", "energy_max_MeV"):
            if actual[key] != expected.get(key):
                raise ValueError(f"HET channel definition differs from validated official metadata: {key}.")
        for key in ("header_value_min", "header_value_max"):
            if actual[key] != expected.get(key):
                raise ValueError(f"HET F2 value bounds differ from the validation report: {key}.")

    rows: list[dict[str, Any]] = []
    skipped_comments = 0
    skipped_blank_lines = 0
    for line_number, line in enumerate(lines[marker_index + 1 :], marker_index + 2):
        stripped = line.strip()
        if not stripped:
            skipped_blank_lines += 1
            continue
        if line.lstrip().startswith(";"):
            skipped_comments += 1
            continue
        fields = stripped.split()
        expected_width = 9 + 2 * len(channels)
        if len(fields) != expected_width:
            raise ValueError(
                f"Line {line_number} has {len(fields)} fields; expected {expected_width}."
            )
        if fields[0] != "0":
            raise ValueError(f"Unexpected verse number {fields[0]!r} on line {line_number}.")
        start = parse_utc_date(fields[1:5])
        end = parse_utc_date(fields[5:9])
        if start >= end:
            raise ValueError(f"Invalid interval on line {line_number}.")
        measurements = fields[9:]
        numeric_values = [float(value) for value in measurements]
        rows.append(
            {
                "source_line": line_number,
                "verse": fields[0],
                "start": start,
                "end": end,
                "source_start_fields": fields[1:5],
                "source_end_fields": fields[5:9],
                "numeric_tokens": measurements,
                "numeric_values": numeric_values,
            }
        )

    expected_records = int((header_end - header_start).total_seconds() // 86400)
    if (header_end - header_start).total_seconds() % 86400:
        raise ValueError("Header interval is not an integer number of days.")
    if len(rows) != expected_records:
        raise ValueError(f"Expected {expected_records} daily records; found {len(rows)}.")
    for index, row in enumerate(rows):
        expected_start = header_start + timedelta(days=index)
        if row["start"] != expected_start or row["end"] != expected_start + timedelta(days=1):
            raise ValueError(f"Record {index + 1} is not the expected contiguous daily interval.")
        if index and rows[index - 1]["start"] >= row["start"]:
            raise ValueError("Daily record start timestamps are not strictly increasing.")

    docs_text = (RAW_DIR / DOCUMENTATION_FILE).read_text(encoding="utf-8").lower()
    if "calibration of the het electron channels is not currently correct" not in docs_text:
        raise ValueError("Official HET electron-calibration caveat was not found.")
    if "do not have any background corrections applied" not in docs_text:
        raise ValueError("Official HET background-correction caveat was not found.")
    if "data gaps in these het files are not filled" not in docs_text:
        raise ValueError("Official HET missing-data statement was not found.")
    if "particles/(cm2-sr-sec-mev)" not in docs_text:
        raise ValueError("Official HET intensity units were not found.")

    header = {
        "format": "ASCII List file (SPDF IMPACT HET documented format)",
        "header_start_utc": iso_utc(header_start),
        "header_end_utc": iso_utc(header_end),
        "time_declaration": t2_lines[0],
        "verse_declaration": verse_lines[0],
        "channel_count": len(channels),
        "record_count": len(rows),
        "skipped_comment_lines": skipped_comments,
        "skipped_blank_lines": skipped_blank_lines,
        "raw_size_bytes": len(raw_bytes),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
    }
    return rows, {
        "channels": channels,
        "header": header,
        "validation": validation,
    }


def _csv_fieldnames(channels: list[dict[str, Any]]) -> list[str]:
    fields = ["verse", "record_start_utc", "record_end_utc"]
    for channel in channels:
        fields.extend((channel["intensity_field"], channel["uncertainty_field"]))
    return fields


def _write_compressed_csv(path: Path, channels: list[dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    with path.open("wb") as raw_output:
        with gzip.GzipFile(fileobj=raw_output, mode="wb", filename="", mtime=0, compresslevel=9) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text_output:
                writer = csv.writer(text_output, lineterminator="\n")
                writer.writerow(_csv_fieldnames(channels))
                for row in rows:
                    values: list[str] = [
                        row["verse"],
                        iso_utc(row["start"]),
                        iso_utc(row["end"]),
                    ]
                    values.extend(row["numeric_tokens"])
                    writer.writerow(values)


def _statistics(values: list[float], header_min: float, header_max: float) -> dict[str, Any]:
    finite = [value for value in values if math.isfinite(value)]
    return {
        "valid_value_count": len(finite),
        "missing_value_count": 0,
        "nonfinite_value_count": len(values) - len(finite),
        "minimum": min(finite) if finite else None,
        "maximum": max(finite) if finite else None,
        "mean": statistics.fmean(finite) if finite else None,
        "median": statistics.median(finite) if finite else None,
        "values_below_F2_header_min": sum(value < header_min for value in finite),
        "values_above_F2_header_max": sum(value > header_max for value in finite),
    }


def process() -> dict[str, Any]:
    required = (RAW_DIR / DATA_FILE, RAW_DIR / README_FILE, RAW_DIR / DOCUMENTATION_FILE, VALIDATION_REPORT)
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required STEREO HET source files are missing: {missing}.")
    source_hashes_before = {
        path.name: sha256_file(path)
        for path in sorted(RAW_DIR.iterdir())
        if path.is_file()
    }
    rows, parsed = _read_sources()
    channels: list[dict[str, Any]] = parsed["channels"]
    header: dict[str, Any] = parsed["header"]
    validation: dict[str, Any] = parsed["validation"]
    if header["raw_sha256"] != source_hashes_before[DATA_FILE]:
        raise RuntimeError("The source data changed while it was being read.")

    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / OUTPUT_CSV
    metadata_path = output_dir / METADATA_FILE
    summary_path = output_dir / SUMMARY_FILE

    fd, temporary_name = tempfile.mkstemp(prefix=OUTPUT_CSV, suffix=".tmp", dir=output_dir)
    os.close(fd)
    temporary_csv = Path(temporary_name)
    try:
        _write_compressed_csv(temporary_csv, channels, rows)
        with gzip.open(temporary_csv, "rt", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != _csv_fieldnames(channels):
                raise ValueError("Processed CSV field names differ from the channel definitions.")
            reopened = list(reader)
        if len(reopened) != len(rows):
            raise ValueError("Processed CSV record count differs from the original ASCII file.")
        for index, (original, processed) in enumerate(zip(rows, reopened)):
            expected_values = [
                original["verse"],
                iso_utc(original["start"]),
                iso_utc(original["end"]),
                *original["numeric_tokens"],
            ]
            actual_values = [processed[name] for name in reader.fieldnames or []]
            if actual_values != expected_values:
                raise ValueError(f"Processed CSV data differs from source record {index + 1}.")
        os.replace(temporary_csv, csv_path)
    finally:
        if temporary_csv.exists():
            temporary_csv.unlink()

    channel_summaries: dict[str, Any] = {}
    for channel_index, channel in enumerate(channels):
        intensities = [row["numeric_values"][channel_index * 2] for row in rows]
        uncertainties = [row["numeric_values"][channel_index * 2 + 1] for row in rows]
        intensity_stats = _statistics(
            intensities, channel["header_value_min"], channel["header_value_max"]
        )
        uncertainty_stats = _statistics(
            uncertainties, channel["header_value_min"], channel["header_value_max"]
        )
        channel_summaries[channel["name"]] = {
            **channel,
            "intensity": intensity_stats,
            "uncertainty": uncertainty_stats,
        }

    all_numeric_values = [
        value for row in rows for value in row["numeric_values"]
    ]
    summary = {
        "dataset_name": "STEREO-A IMPACT HET daily electron/proton intensities",
        "source_file": DATA_FILE,
        "processed_file": OUTPUT_CSV,
        "processing_validation_status": "PASS",
        "source_validation_status": validation["status"],
        "record_count": len(rows),
        "header_time_coverage_utc": {
            "start": header["header_start_utc"],
            "end": header["header_end_utc"],
        },
        "observed_interval_coverage_utc": {
            "start": iso_utc(rows[0]["start"]),
            "end": iso_utc(rows[-1]["end"]),
        },
        "record_intervals_are_daily_and_contiguous": True,
        "electron_channel_count": sum(channel["particle"] == "electron" for channel in channels),
        "proton_channel_count": sum(channel["particle"] == "proton" for channel in channels),
        "channel_count": len(channels),
        "intensity_units": UNITS,
        "uncertainty_units": UNITS,
        "numeric_value_count": len(all_numeric_values),
        "nonfinite_numeric_value_count": sum(not math.isfinite(value) for value in all_numeric_values),
        "documented_missing_sentinel": None,
        "missing_value_handling": (
            "Neither the official HET documentation nor this ASCII product defines a numeric "
            "missing-value sentinel. No sentinel is assumed; source tokens are preserved. "
            "Data gaps are not filled."
        ),
        "verse_values": sorted({row["verse"] for row in rows}),
        "quality_flags": "No separate quality-flag field is defined in this product; verse is 0 for each record.",
        "channels": channel_summaries,
        "source_validation_report_warnings": validation.get("warnings", []),
        "scientific_limitations": [
            "Measurements were collected by STEREO-A at its spacecraft location, not at the Moon.",
            "Particle intensities are not lunar surface measurements or astronaut radiation dose.",
            "Do not convert particle intensities into astronaut dose.",
            "This 2012 sample is historical and does not represent current space weather.",
            "The official HET guide warns that electron-channel calibration is incorrect; do not use these data to estimate electron/proton intensity ratios or derive electron spectra.",
            "No background corrections are applied; background may contribute during quiet conditions.",
        ],
    }

    metadata = {
        "dataset_name": "STEREO-A IMPACT HET daily electron/proton intensities",
        "dataset_id": "STEREO-A/IMPACT/HET/AeH12Mar.1d",
        "spacecraft": "STEREO-A (Ahead)",
        "instrument": "IMPACT High Energy Telescope (HET)",
        "product": "Level 2 1-day averaged ASCII List file",
        "source_urls": validation["source_urls"],
        "source_file": DATA_FILE,
        "source_format": header["format"],
        "source_file_size_bytes": header["raw_size_bytes"],
        "source_sha256": header["raw_sha256"],
        "source_files_sha256": source_hashes_before,
        "source_header": {
            key: value for key, value in header.items() if key != "raw_bytes"
        },
        "time": {
            "timezone": "UTC",
            "encoding": "Header and record timestamps use YYYY Mon D HHMM; output uses ISO-8601 UTC.",
            "record_start_field": "T2 start date/time",
            "record_end_field": "T2 end date/time",
            "time_coverage_utc": {
                "start": header["header_start_utc"],
                "end": header["header_end_utc"],
            },
            "record_count": len(rows),
            "resolution": "1 day",
        },
        "channel_count": len(channels),
        "electron_channel_count": sum(channel["particle"] == "electron" for channel in channels),
        "proton_channel_count": sum(channel["particle"] == "proton" for channel in channels),
        "channels": channels,
        "record_layout": {
            "verse_field": 1,
            "record_start_utc_fields_1_based": [2, 5],
            "record_end_utc_fields_1_based": [6, 9],
            "channel_values": "Each F2 channel is represented by intensity followed by one-sigma uncertainty.",
            "source_data_field_count": 37,
            "quality_flags": "No separate quality-flag field is defined.",
        },
        "missing_value_policy": (
            "The official HET guide states that gaps in the HET files are not filled and does not "
            "define a numeric sentinel for this ASCII product. No sentinel is assumed. Original "
            "numeric tokens are preserved in the compressed CSV; non-finite values, if present, "
            "are counted separately and not substituted."
        ),
        "processing_script": "datasets/scripts/process_stereo_impact.py",
        "processing_script_version": SCRIPT_VERSION,
        "processed_file": OUTPUT_CSV,
        "processed_format": "Deterministic gzip-compressed CSV; source numeric tokens are preserved verbatim.",
        "processed_size_bytes": csv_path.stat().st_size,
        "processed_sha256": sha256_file(csv_path),
        "processed_csv_reopened_and_compared_to_source": True,
        "source_validation_status": validation["status"],
        "source_validation_report_preserved": True,
        "raw_files_sha256_unchanged": source_hashes_before
        == {
            path.name: sha256_file(path)
            for path in sorted(RAW_DIR.iterdir())
            if path.is_file()
        },
        "official_documentation_caveats": [
            "HET electron-channel calibration is not currently correct; electron/proton ratios and electron spectra should not be derived from these data.",
            "No background corrections are applied.",
            "Data gaps are not filled.",
        ],
    }
    if not metadata["raw_files_sha256_unchanged"]:
        raise RuntimeError("One or more original STEREO raw files changed during processing.")

    for path, payload in ((metadata_path, metadata), (summary_path, summary)):
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    return {"metadata": metadata, "summary": summary}


if __name__ == "__main__":
    result = process()
    summary = result["summary"]
    print(
        f"STEREO-A HET processing complete: {summary['record_count']} daily records, "
        f"{summary['electron_channel_count']} electron channels, "
        f"{summary['proton_channel_count']} proton channels."
    )
    for name in (OUTPUT_CSV, METADATA_FILE, SUMMARY_FILE):
        path = OUTPUT_DIR / name
        print(f"{path}: {path.stat().st_size} bytes")
