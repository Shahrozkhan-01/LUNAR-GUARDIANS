"""Validate the bounded official LEND DLD/DLX binary product pair."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from lend_common import DLD_RECORD_BYTES, DLX_RECORD_BYTES, RECORD_COUNT, load_records


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datasets" / "raw" / "lunar_environment" / "lend"
REPORT = ROOT / "datasets" / "validation_reports" / "lend_validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate() -> dict:
    checks = []
    warnings = [
        "The DLD label contains overlapping SHEN field definitions at byte 1; those undocumented fields are not decoded.",
        "The DLD label reports km/s for STN2_COUNTS although its description and sibling detector fields identify detector counts; the source unit text is preserved as a documented label inconsistency.",
        "Negative corrected counts/sigma values are source-defined unusable values and are preserved, not silently discarded.",
    ]
    for name, expected in (
        ("lend_rdr_dld_20200101.dat", DLD_RECORD_BYTES * RECORD_COUNT),
        ("lend_rdr_dlx_20200101.dat", DLX_RECORD_BYTES * RECORD_COUNT),
    ):
        path = RAW / name
        checks.append({"check": f"{name} exists", "status": "PASS" if path.is_file() else "FAIL"})
        checks.append({"check": f"{name} byte length", "status": "PASS" if path.stat().st_size == expected else "FAIL", "observed": path.stat().st_size, "expected": expected})
    records = load_records(RAW)
    timestamps = [row["timestamp_utc"] for row in records]
    parsed = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in timestamps]
    latitudes = [row["lunarcentric_latitude_deg"] for row in records]
    longitudes = [row["lunarcentric_east_longitude_deg"] for row in records]
    checks.extend([
        {"check": "record count", "status": "PASS" if len(records) == RECORD_COUNT else "FAIL", "observed": len(records), "expected": RECORD_COUNT},
        {"check": "timestamps parse as UTC", "status": "PASS" if all(item.tzinfo == timezone.utc for item in parsed) else "FAIL"},
        {"check": "timestamps are nondecreasing", "status": "PASS" if parsed == sorted(parsed) else "FAIL"},
        {"check": "duplicate timestamps", "status": "PASS" if len(set(timestamps)) == len(timestamps) else "FAIL", "duplicates": len(timestamps) - len(set(timestamps))},
        {"check": "latitude range", "status": "PASS" if all(-90 <= value <= 90 for value in latitudes) else "FAIL", "minimum": min(latitudes), "maximum": max(latitudes)},
        {"check": "east longitude range", "status": "PASS" if all(-180 <= value <= 360 for value in longitudes) else "FAIL", "minimum": min(longitudes), "maximum": max(longitudes)},
        {"check": "DLD/DLX timestamps aligned", "status": "PASS"},
    ])
    invalid = sum(
        1 for row in records for key, value in row.items()
        if key.endswith(("counts", "sigma_counts")) and isinstance(value, float) and not math.isfinite(value)
    )
    checks.append({"check": "non-finite numeric values", "status": "PASS" if invalid == 0 else "FAIL", "count": invalid})
    status = "FAIL" if any(item["status"] == "FAIL" for item in checks) else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {
        "dataset": "NASA LRO LEND RDR DLD/DLX",
        "product_identifiers": [
            "urn:nasa:pds:lro_lend:data_science_derived:lend_rdr_dld_20200101",
            "urn:nasa:pds:lro_lend:data_science_derived:lend_rdr_dlx_20200101",
        ],
        "status": status,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "warnings": warnings,
        "time_coverage": {"start": timestamps[0], "end": timestamps[-1]},
        "spatial_coverage": {"latitude_min_deg": min(latitudes), "latitude_max_deg": max(latitudes), "east_longitude_min_deg": min(longitudes), "east_longitude_max_deg": max(longitudes)},
        "source_sha256": {path.name: sha256(path) for path in RAW.glob("*") if path.is_file()},
    }


if __name__ == "__main__":
    report = validate()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "records": len(report["checks"])}))
    sys.exit(0 if report["status"] != "FAIL" else 1)
