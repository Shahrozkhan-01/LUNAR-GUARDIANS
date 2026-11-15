"""Convert the validated Diviner PDS3 fixed-width table to deterministic CSV.GZ."""

from __future__ import annotations

from array import array
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "lunar_environment" / "diviner"
OUTPUT_DIR = ROOT / "datasets" / "processed" / "lunar_environment" / "diviner"
DATA_FILE = "global_cumul_avg_cyl_80s70s_002.tab"
LABEL_FILE = "global_cumul_avg_cyl_80s70s_002.lbl"
FORMAT_FILE = "dlre_gcp.fmt"
OUTPUT_FILE = "global_cumul_avg_cyl_80s70s_002.csv.gz"
METADATA_FILE = "diviner_processing_metadata.json"
SUMMARY_FILE = "diviner_summary_statistics.json"
UNKNOWN_VALUE = -9999.0
INVALID_VALUE = -9998.0
TEMPERATURE_COLUMNS = {"t3", "t4", "t5", "t6", "t7", "t8", "t9", "tbol"}
NORMALIZED_NAMES = {
    "clon": "center_longitude_deg",
    "clat": "center_latitude_deg",
    "ltim": "local_time_hour",
    **{
        f"t{channel}": f"brightness_temperature_channel_{channel}_k"
        for channel in range(3, 10)
    },
    "tbol": "brightness_temperature_bolometric_k",
}


def _label_value(label: str, key: str) -> str | None:
    match = re.search(
        rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$",
        label,
    )
    return match.group(1).strip().strip('"') if match else None


def _format_columns(format_text: str) -> list[dict[str, Any]]:
    columns: list[dict[str, Any]] = []
    for block in re.findall(
        r"(?is)OBJECT\s*=\s*COLUMN(.*?)END_OBJECT\s*=\s*COLUMN",
        format_text,
    ):
        column: dict[str, Any] = {}
        for key in (
            "NAME",
            "START_BYTE",
            "BYTES",
            "UNIT",
            "DATA_TYPE",
            "DESCRIPTION",
            "UNKNOWN_CONSTANT",
            "INVALID_CONSTANT",
        ):
            if key == "DESCRIPTION":
                match = re.search(
                    r'(?ims)^\s*DESCRIPTION\s*=\s*"(.+?)"\s*$',
                    block,
                )
            else:
                match = re.search(rf"(?im)^\s*{key}\s*=\s*(.+?)\s*$", block)
            if match:
                column[key.lower()] = match.group(1).strip().strip('"')
        if {"name", "start_byte", "bytes", "unit"} - column.keys():
            raise ValueError(f"Incomplete PDS format column definition: {column}")
        column["start_byte"] = int(column["start_byte"])
        column["bytes"] = int(column["bytes"])
        columns.append(column)
    if not columns:
        raise ValueError("No COLUMN definitions found in the PDS format file.")
    return columns


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _select_nth(values: array, index: int) -> float:
    """Select an order statistic in-place without making a second value copy."""
    low = 0
    high = len(values) - 1
    while low < high:
        middle = (low + high) // 2
        candidates = sorted((values[low], values[middle], values[high]))
        pivot = candidates[1]
        less = low
        scan = low
        greater = high
        while scan <= greater:
            if values[scan] < pivot:
                values[less], values[scan] = values[scan], values[less]
                less += 1
                scan += 1
            elif values[scan] > pivot:
                values[scan], values[greater] = values[greater], values[scan]
                greater -= 1
            else:
                scan += 1
        if index < less:
            high = less - 1
        elif index > greater:
            low = greater + 1
        else:
            return values[index]
    return values[low]


def _median(values: array) -> float | None:
    if not values:
        return None
    middle = len(values) // 2
    upper = _select_nth(values, middle)
    if len(values) % 2:
        return upper
    lower = _select_nth(values, middle - 1)
    return (lower + upper) / 2.0


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_gzip_csv(path: Path, columns: list[dict[str, Any]], rows: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as raw_output:
        with gzip.GzipFile(
            filename="",
            fileobj=raw_output,
            mode="wb",
            compresslevel=6,
            mtime=0,
        ) as compressed:
            with io.TextIOWrapper(compressed, encoding="ascii", newline="") as text:
                writer = csv.writer(text, lineterminator="\n")
                writer.writerow([NORMALIZED_NAMES[column["name"]] for column in columns])
                for values in rows:
                    writer.writerow(values)
    os.replace(temporary, path)


def _validate_processed_output(
    output_path: Path,
    data_path: Path,
    record_bytes: int,
    columns: list[dict[str, Any]],
    expected_rows: int,
) -> int:
    expected_names = [NORMALIZED_NAMES[column["name"]] for column in columns]
    verified_rows = 0
    with data_path.open("rb") as source, gzip.open(
        output_path, "rt", encoding="ascii", newline=""
    ) as processed:
        reader = csv.reader(processed)
        if next(reader, None) != expected_names:
            raise ValueError("Processed CSV header does not match normalized PDS columns.")
        source_header = source.read(record_bytes)
        source_names = [
            value.strip().decode("ascii")
            for value in source_header.rstrip(b"\r\n").split(b",")
        ]
        if source_names != [column["name"] for column in columns]:
            raise ValueError("Raw table header changed before output readback verification.")

        for row_number in range(1, expected_rows + 1):
            source_record = source.read(record_bytes)
            output_row = next(reader, None)
            if len(source_record) != record_bytes or output_row is None:
                raise ValueError(f"Readback ended before source row {row_number}.")
            if len(output_row) != len(columns):
                raise ValueError(f"Processed row {row_number} has the wrong number of columns.")
            for index, column in enumerate(columns):
                start = column["start_byte"] - 1
                source_value = source_record[
                    start : start + column["bytes"]
                ].decode("ascii").strip()
                numeric_value = float(source_value)
                expected_value = (
                    ""
                    if numeric_value in (UNKNOWN_VALUE, INVALID_VALUE)
                    else source_value
                )
                if output_row[index] != expected_value:
                    raise ValueError(
                        f"Processed value differs from source at row {row_number}, "
                        f"column {column['name']}."
                    )
            verified_rows += 1

        if source.read():
            raise ValueError("Raw source has trailing bytes during output readback verification.")
        if next(reader, None) is not None:
            raise ValueError("Processed CSV contains extra rows after the expected row count.")
    return verified_rows


def process() -> dict[str, Any]:
    data_path = RAW_DIR / DATA_FILE
    label_path = RAW_DIR / LABEL_FILE
    format_path = RAW_DIR / FORMAT_FILE
    required = (data_path, label_path, format_path)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required Diviner source files are missing: {missing}")

    original_sha256 = _sha256_file(data_path)
    label = label_path.read_text(encoding="ascii")
    format_text = format_path.read_text(encoding="ascii")
    columns = _format_columns(format_text)
    record_bytes = int(_label_value(label, "RECORD_BYTES") or 0)
    file_records = int(_label_value(label, "FILE_RECORDS") or 0)
    table_rows_match = re.search(r"(?im)^\s*ROWS\s*=\s*(\d+)", label)
    table_columns_match = re.search(r"(?im)^\s*COLUMNS\s*=\s*(\d+)", label)
    pointer_match = re.search(
        r"(?im)^\s*\^TABLE\s*=\s*\([^,]+,\s*(\d+)\s*\)",
        label,
    )
    if not all((table_rows_match, table_columns_match, pointer_match)):
        raise ValueError("PDS label is missing table row/column counts or table pointer.")
    expected_rows = int(table_rows_match.group(1))
    expected_columns = int(table_columns_match.group(1))
    table_offset = (int(pointer_match.group(1)) - 1) * record_bytes
    if record_bytes <= 0 or table_offset != record_bytes:
        raise ValueError("Expected a single fixed-length PDS header record.")
    if len(columns) != expected_columns:
        raise ValueError(
            f"PDS format defines {len(columns)} columns; label declares {expected_columns}."
        )
    if [column["name"] for column in columns] != list(NORMALIZED_NAMES):
        raise ValueError("PDS format column names differ from the documented Diviner schema.")
    for column in columns:
        if column["start_byte"] - 1 + column["bytes"] > record_bytes:
            raise ValueError(f"Column exceeds PDS record width: {column['name']}")

    expected_size = record_bytes * file_records
    if data_path.stat().st_size != expected_size:
        raise ValueError(
            f"Raw table size is {data_path.stat().st_size}; PDS label specifies {expected_size}."
        )

    bounds = {
        "clon": (-180.0, 180.0),
        "clat": (
            float((_label_value(label, "MINIMUM_LATITUDE") or "").split()[0]),
            float((_label_value(label, "MAXIMUM_LATITUDE") or "").split()[0]),
        ),
        "ltim": (0.0, 24.0),
    }
    statistics: dict[str, dict[str, Any]] = {
        column["name"]: {
            "unit": column["unit"],
            "description": " ".join(column.get("description", "").split()),
            "valid_count": 0,
            "unknown_missing_count": 0,
            "invalid_sentinel_count": 0,
            "minimum": None,
            "maximum": None,
            "sum": 0.0,
            "negative_brightness_value_count": 0,
        }
        for column in columns
    }
    temperature_values = {name: array("d") for name in TEMPERATURE_COLUMNS}
    unique_coordinates: dict[str, set[float]] = {
        "clon": set(),
        "clat": set(),
        "ltim": set(),
    }
    local_time_distribution: dict[str, int] = {}
    rows_with_missing = 0
    rows_with_invalid = 0
    rows_written = 0

    def normalized_rows() -> Any:
        nonlocal rows_with_missing, rows_with_invalid, rows_written
        with data_path.open("rb") as source:
            header = source.read(record_bytes)
            header_names = [
                value.strip().decode("ascii")
                for value in header.rstrip(b"\r\n").split(b",")
            ]
            expected_names = [column["name"] for column in columns]
            if len(header) != record_bytes or header_names != expected_names:
                raise ValueError("PDS table header does not match the format definition.")

            for row_number in range(1, expected_rows + 1):
                record = source.read(record_bytes)
                if len(record) != record_bytes:
                    raise ValueError(
                        f"Short PDS record at row {row_number}: {len(record)} of {record_bytes} bytes."
                    )
                if any(byte > 127 for byte in record):
                    raise ValueError(f"Non-ASCII byte found at PDS row {row_number}.")

                output_values: list[str] = []
                row_has_missing = False
                row_has_invalid = False
                parsed: dict[str, float] = {}
                for column in columns:
                    name = column["name"]
                    start = column["start_byte"] - 1
                    raw_value = record[start : start + column["bytes"]].decode("ascii").strip()
                    try:
                        value = float(raw_value)
                    except ValueError as exc:
                        raise ValueError(
                            f"Unparseable {name} value at PDS row {row_number}: {raw_value!r}"
                        ) from exc
                    if not math.isfinite(value):
                        raise ValueError(f"Non-finite {name} value at PDS row {row_number}.")

                    parsed[name] = value
                    column_stats = statistics[name]
                    if value == UNKNOWN_VALUE or value == INVALID_VALUE:
                        output_values.append("")
                        row_has_missing = True
                        if value == UNKNOWN_VALUE:
                            column_stats["unknown_missing_count"] += 1
                        else:
                            column_stats["invalid_sentinel_count"] += 1
                            row_has_invalid = True
                        continue

                    output_values.append(raw_value)
                    column_stats["valid_count"] += 1
                    column_stats["sum"] += value
                    current_minimum = column_stats["minimum"]
                    current_maximum = column_stats["maximum"]
                    column_stats["minimum"] = (
                        value if current_minimum is None else min(current_minimum, value)
                    )
                    column_stats["maximum"] = (
                        value if current_maximum is None else max(current_maximum, value)
                    )
                    if name in TEMPERATURE_COLUMNS:
                        temperature_values[name].append(value)
                        if value < 0:
                            column_stats["negative_brightness_value_count"] += 1
                    if name in unique_coordinates:
                        minimum, maximum = bounds[name]
                        if not minimum <= value <= maximum:
                            row_has_invalid = True
                        unique_coordinates[name].add(value)
                    if name == "ltim":
                        time_key = format(value, ".8g")
                        local_time_distribution[time_key] = (
                            local_time_distribution.get(time_key, 0) + 1
                        )

                rows_with_missing += row_has_missing
                rows_with_invalid += row_has_invalid
                rows_written += 1
                yield output_values

            trailing = source.read()
            if trailing:
                raise ValueError(f"Raw PDS table has {len(trailing)} unexpected trailing bytes.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILE
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        _write_gzip_csv(output_path, columns, normalized_rows())
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise

    if rows_written != expected_rows:
        raise ValueError(f"Wrote {rows_written} rows; PDS label declares {expected_rows}.")
    readback_rows = _validate_processed_output(
        output_path,
        data_path,
        record_bytes,
        columns,
        expected_rows,
    )
    if readback_rows != expected_rows:
        raise ValueError(
            f"Read back {readback_rows} processed rows; expected {expected_rows}."
        )
    if _sha256_file(data_path) != original_sha256:
        raise RuntimeError("Raw Diviner source hash changed during processing.")

    for name, column_stats in statistics.items():
        count = column_stats["valid_count"]
        column_stats["mean"] = column_stats["sum"] / count if count else None
        del column_stats["sum"]
        column_stats["median"] = (
            _median(temperature_values[name]) if name in TEMPERATURE_COLUMNS else None
        )

    coverage = {
        "center_longitude_degrees": {
            "minimum": min(unique_coordinates["clon"]),
            "maximum": max(unique_coordinates["clon"]),
            "unique_level_count": len(unique_coordinates["clon"]),
        },
        "center_planetocentric_latitude_degrees": {
            "minimum": min(unique_coordinates["clat"]),
            "maximum": max(unique_coordinates["clat"]),
            "unique_level_count": len(unique_coordinates["clat"]),
        },
        "local_time_hours": {
            "minimum": min(unique_coordinates["ltim"]),
            "maximum": max(unique_coordinates["ltim"]),
            "unique_level_count": len(unique_coordinates["ltim"]),
            "bin_counts": {
                key: local_time_distribution[key]
                for key in sorted(local_time_distribution, key=float)
            },
        },
    }
    processed_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "dataset_name": "LRO Diviner Global Cumulative Average Product",
        "data_set_id": _label_value(label, "DATA_SET_ID"),
        "product_id": _label_value(label, "PRODUCT_ID"),
        "source_file": DATA_FILE,
        "source_sha256": original_sha256,
        "source_size_bytes": data_path.stat().st_size,
        "source_format": "PDS3 fixed-length ASCII table",
        "source_record_bytes": record_bytes,
        "source_row_count": expected_rows,
        "processed_row_count": rows_written,
        "processed_output_readback_verified": True,
        "processed_output_rows_read_back": readback_rows,
        "processed_at_utc": processed_at,
        "processing_script": "datasets/scripts/process_diviner_dataset.py",
        "processing_script_version": "1.0.0",
        "output_file": OUTPUT_FILE,
        "output_format": "UTF-8 CSV compressed with gzip; deterministic gzip timestamp",
        "output_size_bytes": output_path.stat().st_size,
        "spatial_reference": {
            "latitude_type": "planetocentric",
            "longitude_direction": "positive east",
            "latitude_coverage_degrees": [-80.0, -70.0],
            "longitude_coverage_degrees": [-180.0, 180.0],
        },
        "observation_period": {
            "start": _label_value(label, "START_TIME"),
            "stop": _label_value(label, "STOP_TIME"),
        },
        "missing_value_policy": {
            "unknown_constant": UNKNOWN_VALUE,
            "invalid_constant": INVALID_VALUE,
            "output_representation": "empty CSV field",
            "note": "Sentinels are replaced with empty fields; valid source values are preserved verbatim.",
        },
        "columns": [
            {
                "source_name": column["name"],
                "output_name": NORMALIZED_NAMES[column["name"]],
                "description": " ".join(column.get("description", "").split()),
                "source_data_type": column.get("data_type", ""),
                "logical_output_type": "nullable float64",
                "unit": column["unit"],
                "start_byte_1_based": column["start_byte"],
                "width_bytes": column["bytes"],
            }
            for column in columns
        ],
        "raw_integrity_verified_unchanged": True,
    }
    summary = {
        "dataset_name": metadata["dataset_name"],
        "source_sha256": original_sha256,
        "processed_file": OUTPUT_FILE,
        "processed_row_count": rows_written,
        "processed_output_readback_verified": True,
        "processed_output_rows_read_back": readback_rows,
        "row_quality": {
            "rows_with_any_documented_missing_or_invalid_sentinel": rows_with_missing,
            "rows_with_documented_invalid_sentinel_or_coordinate_out_of_bounds": rows_with_invalid,
            "rows_without_documented_invalid_sentinel_or_coordinate_out_of_bounds": (
                rows_written - rows_with_invalid
            ),
            "invalid_sentinel_count_by_column": {
                name: values["invalid_sentinel_count"]
                for name, values in statistics.items()
            },
        },
        "missing_value_counts_by_column": {
            name: values["unknown_missing_count"]
            for name, values in statistics.items()
        },
        "columns": statistics,
        "coverage": coverage,
        "brightness_temperature_interpretation": (
            "t3-t9 and tbol are calibrated brightness temperatures in kelvin, "
            "not ordinary air temperature or in-situ habitat temperature. "
            "Negative values are preserved as documented by the PDS label."
        ),
        "spatial_temporal_scope": {
            "latitude_band": "70 degrees south to 80 degrees south",
            "longitude": "all longitudes, -180 to 180 degrees east-positive convention",
            "observation_period": metadata["observation_period"],
            "binning": "0.5 degree latitude/longitude and 0.25 hour local time",
        },
    }
    _write_json(OUTPUT_DIR / METADATA_FILE, metadata)
    _write_json(OUTPUT_DIR / SUMMARY_FILE, summary)
    return {"metadata": metadata, "summary": summary}


if __name__ == "__main__":
    result = process()
    summary = result["summary"]
    print(
        "Diviner processing complete: "
        f"{summary['processed_row_count']} rows; "
        f"{summary['row_quality']['rows_with_any_documented_missing_or_invalid_sentinel']} "
        "rows contain documented missing/invalid sentinels."
    )
    for filename in (OUTPUT_FILE, METADATA_FILE, SUMMARY_FILE):
        path = OUTPUT_DIR / filename
        print(f"{path}: {path.stat().st_size} bytes")
