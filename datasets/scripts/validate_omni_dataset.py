"""Validate the bounded NASA OMNI2 hourly source selection."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from omni_common import FIELDS, is_missing, iter_records

ROOT = SCRIPT_DIR.parents[1]
SOURCE = ROOT / "datasets/raw/space_weather/omni/omni2_2020.dat"
REPORT = ROOT / "datasets/validation_reports/omni_hourly_validation.json"
START = datetime(2020, 1, 1, tzinfo=timezone.utc)
END = datetime(2020, 2, 1, tzinfo=timezone.utc)


def main() -> int:
    records = []
    malformed = []
    try:
        for line_number, record in iter_records(SOURCE):
            if START <= datetime.fromisoformat(record["timestamp_utc"].replace("Z", "+00:00")) < END:
                records.append(record)
    except ValueError as exc:
        malformed.append(str(exc))

    timestamps = [record["timestamp_utc"] for record in records]
    duplicate_timestamps = sorted(
        timestamp for timestamp, count in Counter(timestamps).items() if count > 1
    )
    expected = 31 * 24
    missing_counts = {
        name: sum(is_missing(name, record[name]) for record in records)
        for name, _ in FIELDS
    }
    invalid_ranges = []
    for record in records:
        if record["hour"] not in range(24) or record["day_of_year"] not in range(1, 367):
            invalid_ranges.append(record["timestamp_utc"])
        if record["solar_wind_speed_km_s"] != 9999 and not 0 <= record["solar_wind_speed_km_s"] <= 3000:
            invalid_ranges.append(record["timestamp_utc"] + ":solar_wind_speed")

    continuity_gaps = []
    for previous, current in zip(records, records[1:]):
        previous_time = datetime.fromisoformat(previous["timestamp_utc"].replace("Z", "+00:00"))
        current_time = datetime.fromisoformat(current["timestamp_utc"].replace("Z", "+00:00"))
        if current_time - previous_time != timedelta(hours=1):
            continuity_gaps.append({"previous": previous["timestamp_utc"], "current": current["timestamp_utc"]})

    warnings = []
    if any(missing_counts.values()):
        warnings.append("Official OMNI fill values are present and retained; they are not silently discarded.")
    if expected != len(records):
        warnings.append(f"Expected {expected} bounded hourly records but found {len(records)}.")
    status = "FAIL" if malformed or duplicate_timestamps or invalid_ranges or len(records) != expected else (
        "PASS_WITH_WARNINGS" if warnings else "PASS"
    )
    report = {
        "dataset": "NASA OMNI2 hourly data",
        "source_file": str(SOURCE.relative_to(ROOT)),
        "selection": {"start_utc": START.isoformat().replace("+00:00", "Z"), "end_utc_exclusive": END.isoformat().replace("+00:00", "Z")},
        "status": status,
        "record_count": len(records),
        "expected_record_count": expected,
        "time_coverage": {"first": timestamps[0] if timestamps else None, "last": timestamps[-1] if timestamps else None},
        "timestamp_continuity_gaps": continuity_gaps,
        "duplicate_timestamps": duplicate_timestamps,
        "malformed_records": malformed,
        "missing_value_counts": missing_counts,
        "invalid_values": invalid_ranges,
        "units": "Official OMNI2 field definitions in raw/space_weather/omni/omni2.text",
        "warnings": warnings,
        "fill_value_policy": "The official numeric fill values are preserved in raw and processed records.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "records": len(records), "report": str(REPORT)}, indent=2))
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
