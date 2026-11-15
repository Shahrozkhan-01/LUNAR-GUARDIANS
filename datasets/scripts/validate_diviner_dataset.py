#!/usr/bin/env python
"""Validate a raw PDS3 fixed-width Diviner GCP ASCII table without modifying it."""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = (
    REPOSITORY_ROOT / "datasets" / "raw" / "lunar_environment" / "diviner"
)
DEFAULT_REPORT = (
    REPOSITORY_ROOT
    / "datasets"
    / "validation_reports"
    / "diviner_gcp_80s70s_validation.json"
)
TEMPERATURE_COLUMNS = {"t3", "t4", "t5", "t6", "t7", "t8", "t9", "tbol"}
GRID_SPACING = {
    "clon": (-179.75, 0.5),
    "clat": (-79.75, 0.5),
    "ltim": (0.125, 0.25),
}
GRID_TOLERANCE = {"clon": 1e-5, "clat": 1e-5, "ltim": 0.006}
EXPECTED_GRID_LEVELS = {"clon": 720, "clat": 20, "ltim": 96}


def _label_value(label: str, key: str) -> str | None:
    match = re.search(
        rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$",
        label,
    )
    if not match:
        return None
    return match.group(1).strip().strip('"')


def _format_columns(format_text: str) -> list[dict[str, Any]]:
    columns = []
    for block in re.findall(
        r"(?is)OBJECT\s*=\s*COLUMN(.*?)END_OBJECT\s*=\s*COLUMN",
        format_text,
    ):
        column: dict[str, Any] = {}
        for key in ("NAME", "START_BYTE", "BYTES", "UNIT", "UNKNOWN_CONSTANT", "INVALID_CONSTANT"):
            match = re.search(rf"(?im)^\s*{key}\s*=\s*(.+?)\s*$", block)
            if match:
                column[key.lower()] = match.group(1).strip().strip('"')
        if {"name", "start_byte", "bytes"} - column.keys():
            raise ValueError(f"Incomplete PDS format column definition: {column}")
        column["start_byte"] = int(column["start_byte"])
        column["bytes"] = int(column["bytes"])
        column["unit"] = column.get("unit", "")
        column["sentinels"] = {
            float(column[key])
            for key in ("unknown_constant", "invalid_constant")
            if key in column
        }
        columns.append(column)
    if not columns:
        raise ValueError("No COLUMN definitions found in the PDS format file.")
    return columns


def validate_dataset(data_path: Path, label_path: Path, format_path: Path) -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat()
    report: dict[str, Any] = {
        "dataset_name": "LRO Diviner Global Cumulative Average Product",
        "file": str(data_path),
        "checked_at_utc": checked_at,
        "file_exists": data_path.is_file(),
        "file_size_bytes": data_path.stat().st_size if data_path.is_file() else None,
        "file_format": "PDS3 fixed-length ASCII table (PDS format definition)",
        "checks": {},
        "columns": {},
        "errors": [],
        "warnings": [],
    }

    for required in (data_path, label_path, format_path):
        if not required.is_file():
            report["errors"].append(f"Required file is missing: {required}")
    if report["errors"]:
        report["validation_status"] = "FAILED"
        return report

    label = label_path.read_text(encoding="ascii", errors="strict")
    format_text = format_path.read_text(encoding="ascii", errors="strict")
    columns = _format_columns(format_text)
    record_bytes = int(_label_value(label, "RECORD_BYTES") or 0)
    file_records = int(_label_value(label, "FILE_RECORDS") or 0)
    table_rows = int(
        re.search(r"(?im)^\s*ROWS\s*=\s*(\d+)", label).group(1)  # type: ignore[union-attr]
    )
    table_columns = int(
        re.search(r"(?im)^\s*COLUMNS\s*=\s*(\d+)", label).group(1)  # type: ignore[union-attr]
    )
    table_pointer = re.search(
        r"(?im)^\s*\^TABLE\s*=\s*\([^,]+,\s*(\d+)\s*\)",
        label,
    )
    if not table_pointer:
        raise ValueError("PDS label does not identify the table's starting record.")
    table_offset = (int(table_pointer.group(1)) - 1) * record_bytes
    expected_size = record_bytes * file_records
    report.update(
        {
            "data_set_id": _label_value(label, "DATA_SET_ID"),
            "product_id": _label_value(label, "PRODUCT_ID"),
            "observation_period": {
                "start": _label_value(label, "START_TIME"),
                "stop": _label_value(label, "STOP_TIME"),
            },
            "geographic_coverage": {
                "minimum_latitude_degrees": float(_label_value(label, "MINIMUM_LATITUDE").split()[0]),  # type: ignore[union-attr]
                "maximum_latitude_degrees": float(_label_value(label, "MAXIMUM_LATITUDE").split()[0]),  # type: ignore[union-attr]
                "westernmost_longitude_degrees": float(_label_value(label, "WESTERNMOST_LONGITUDE").split()[0]),  # type: ignore[union-attr]
                "easternmost_longitude_degrees": float(_label_value(label, "EASTERNMOST_LONGITUDE").split()[0]),  # type: ignore[union-attr]
            },
            "record_bytes": record_bytes,
            "file_records_including_header": file_records,
            "expected_data_rows": table_rows,
            "table_columns": table_columns,
            "table_offset_bytes": table_offset,
            "documented_missing_unknown_value": -9999,
            "documented_invalid_value": -9998,
            "temperature_range_policy": (
                "The PDS GCP label does not specify hard minimum/maximum bounds "
                "for temperature columns. The documented -9999/-9998 sentinels "
                "and numeric finiteness are checked; no arbitrary temperature "
                "limits are imposed. Negative brightness values are documented."
            ),
            "column_definitions": [
                {
                    "name": col["name"],
                    "unit": col["unit"],
                    "start_byte": col["start_byte"],
                    "width_bytes": col["bytes"],
                    "unknown_constant": col.get("unknown_constant"),
                    "invalid_constant": col.get("invalid_constant"),
                }
                for col in columns
            ],
        }
    )

    if record_bytes <= 0 or file_records <= 1:
        report["errors"].append("PDS label has invalid record size or record count.")
        report["validation_status"] = "FAILED"
        return report
    if len(columns) != table_columns:
        report["errors"].append(
            f"PDS format defines {len(columns)} columns; label declares {table_columns}."
        )
    if table_offset != record_bytes:
        report["errors"].append(
            f"Table starts at byte {table_offset}; expected one header record of {record_bytes} bytes."
        )
    if data_path.stat().st_size != expected_size:
        report["errors"].append(
            f"File size is {data_path.stat().st_size} bytes; PDS label requires {expected_size}."
        )
    report["checks"]["file_size_matches_pds_label"] = (
        data_path.stat().st_size == expected_size
    )

    if report["errors"]:
        report["validation_status"] = "FAILED"
        return report

    bounds = report["geographic_coverage"]
    stats = {
        col["name"]: {
            "unit": col["unit"],
            "unknown_or_missing_count": 0,
            "invalid_sentinel_count": 0,
            "non_finite_count": 0,
            "out_of_documented_range_count": 0,
            "off_grid_count": 0,
            "negative_temperature_count": 0,
            "valid_count": 0,
            "minimum": None,
            "maximum": None,
        }
        for col in columns
    }
    actual_rows = 0
    short_or_non_ascii_rows = 0
    seen_coordinates: dict[str, set[float]] = {
        name: set() for name in GRID_SPACING
    }

    with data_path.open("rb") as stream:
        header = stream.read(record_bytes)
        header_names = [
            field.strip().decode("ascii", errors="replace")
            for field in header.rstrip(b"\r\n").split(b",")
        ]
        expected_names = [column["name"] for column in columns]
        report["checks"]["table_header_matches_pds_format"] = (
            len(header) == record_bytes and header_names == expected_names
        )
        if not report["checks"]["table_header_matches_pds_format"]:
            report["errors"].append(
                "First record's column names do not match the PDS format definition."
            )

        for row_number in range(1, table_rows + 1):
            row = stream.read(record_bytes)
            if len(row) != record_bytes:
                short_or_non_ascii_rows += 1
                report["errors"].append(
                    f"Short record at data row {row_number}: {len(row)} of {record_bytes} bytes."
                )
                break
            actual_rows += 1
            if any(byte > 127 for byte in row):
                short_or_non_ascii_rows += 1
                continue

            for column in columns:
                name = column["name"]
                start = column["start_byte"] - 1
                raw_value = row[start : start + column["bytes"]].decode("ascii").strip()
                try:
                    value = float(raw_value)
                except ValueError:
                    stats[name]["non_finite_count"] += 1
                    continue

                if not math.isfinite(value):
                    stats[name]["non_finite_count"] += 1
                    continue
                if value in column["sentinels"]:
                    if value == float(column.get("invalid_constant", "nan")):
                        stats[name]["invalid_sentinel_count"] += 1
                    else:
                        stats[name]["unknown_or_missing_count"] += 1
                    continue

                out_of_range = False
                if name == "clon":
                    out_of_range = not -180.0 <= value <= 180.0
                elif name == "clat":
                    out_of_range = not (
                        bounds["minimum_latitude_degrees"]
                        <= value
                        <= bounds["maximum_latitude_degrees"]
                    )
                elif name == "ltim":
                    out_of_range = not 0.0 <= value < 24.0
                if out_of_range:
                    stats[name]["out_of_documented_range_count"] += 1
                if name in GRID_SPACING:
                    origin, spacing = GRID_SPACING[name]
                    nearest_grid_point = origin + round((value - origin) / spacing) * spacing
                    if abs(value - nearest_grid_point) > GRID_TOLERANCE[name]:
                        stats[name]["off_grid_count"] += 1
                    seen_coordinates[name].add(value)

                if name in TEMPERATURE_COLUMNS and value < 0:
                    # The PDS label explicitly documents negative brightness
                    # temperatures from negative radiance below channel sensitivity.
                    stats[name]["negative_temperature_count"] += 1
                stats[name]["valid_count"] += 1
                current_min = stats[name]["minimum"]
                current_max = stats[name]["maximum"]
                stats[name]["minimum"] = value if current_min is None else min(current_min, value)
                stats[name]["maximum"] = value if current_max is None else max(current_max, value)

    expected_table_bytes = table_rows * record_bytes
    trailing = data_path.stat().st_size - table_offset - expected_table_bytes
    report["checks"].update(
        {
            "data_rows_match_pds_label": actual_rows == table_rows,
            "all_records_are_ascii": short_or_non_ascii_rows == 0,
            "no_unexpected_trailing_bytes": trailing == 0,
            "column_count_matches_format": len(columns) == table_columns,
        }
    )
    report["rows_read"] = actual_rows
    report["unexpected_trailing_bytes"] = trailing
    for name in seen_coordinates:
        report["checks"][f"{name}_coordinates_follow_documented_grid"] = (
            stats[name]["off_grid_count"] == 0
        )
    report["checks"]["coordinates_within_documented_bounds"] = all(
        stats[name]["out_of_documented_range_count"] == 0
        for name in ("clon", "clat", "ltim")
    )
    report["coordinate_grid_levels"] = {
        name: {
            "observed": len(values),
            "expected": EXPECTED_GRID_LEVELS[name],
        }
        for name, values in seen_coordinates.items()
    }
    report["checks"]["coordinate_grid_level_counts_match"] = all(
        len(seen_coordinates[name]) == expected
        for name, expected in EXPECTED_GRID_LEVELS.items()
    )
    if not report["checks"]["coordinate_grid_level_counts_match"]:
        report["errors"].append(
            "Observed coordinate or local-time grid level counts do not match "
            "the documented 0.5-degree and 0.25-hour binning."
        )
    report["columns"] = stats
    if any(stats[name]["negative_temperature_count"] for name in TEMPERATURE_COLUMNS):
        report["warnings"].append(
            "Negative brightness-temperature values are retained and counted; "
            "the PDS label attributes them to negative radiance below a channel's "
            "sensitivity, so they are not treated as invalid."
        )
    report["warnings"].append(
        "The PDS GCP label provides no hard minimum/maximum range for brightness "
        "temperature. No unsupported physical threshold was invented."
    )

    for name, result in stats.items():
        if result["non_finite_count"]:
            report["errors"].append(
                f"{name} has {result['non_finite_count']} unparsable or non-finite values."
            )
        if result["out_of_documented_range_count"]:
            report["errors"].append(
                f"{name} has {result['out_of_documented_range_count']} values outside documented coordinate limits."
            )
        if result["off_grid_count"]:
            report["errors"].append(
                f"{name} has {result['off_grid_count']} coordinate values off its documented grid."
            )
    if actual_rows != table_rows:
        report["errors"].append(
            f"Read {actual_rows} data rows; PDS label declares {table_rows}."
        )
    if short_or_non_ascii_rows:
        report["errors"].append(
            f"{short_or_non_ascii_rows} records were short or contained non-ASCII bytes."
        )
    if trailing != 0:
        report["errors"].append(f"Found {trailing} unexpected trailing bytes.")
    report["validation_status"] = "PASSED" if not report["errors"] else "FAILED"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_RAW_DIR / "global_cumul_avg_cyl_80s70s_002.tab")
    parser.add_argument("--label", type=Path, default=DEFAULT_RAW_DIR / "global_cumul_avg_cyl_80s70s_002.lbl")
    parser.add_argument("--format", type=Path, default=DEFAULT_RAW_DIR / "dlre_gcp.fmt")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    try:
        report = validate_dataset(args.data, args.label, args.format)
    except (OSError, ValueError, AttributeError) as exc:
        report = {
            "dataset_name": "LRO Diviner Global Cumulative Average Product",
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "validation_status": "FAILED",
            "errors": [str(exc)],
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"\nValidation report written to: {args.output}")
    return 0 if report.get("validation_status") == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
