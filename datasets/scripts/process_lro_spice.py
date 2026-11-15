"""Compute a small hourly LRO position sample with NASA NAIF SPICE."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import spiceypy as spice


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datasets" / "raw" / "communication_navigation" / "lro_spice"
OUTPUT = ROOT / "datasets" / "processed" / "communication_navigation" / "lro_spice"
SPK_NAME = "lrorg_2017258_2017349_v01.bsp"
LSK_NAME = "naif0012.tls"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    spice.furnsh(str(RAW / LSK_NAME))
    spice.furnsh(str(RAW / SPK_NAME))
    start = datetime(2017, 9, 15, tzinfo=timezone.utc)
    rows = []
    try:
        for index in range(24):
            timestamp = start + timedelta(hours=index)
            et = spice.str2et(timestamp.strftime("%Y-%m-%dT%H:%M:%S"))
            position, light_time = spice.spkpos("-85", et, "J2000", "NONE", "MOON")
            x, y, z = (float(value) for value in position)
            rows.append(
                {
                    "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                    "x_km": x,
                    "y_km": y,
                    "z_km": z,
                    "distance_from_moon_center_km": (x * x + y * y + z * z) ** 0.5,
                    "one_way_light_time_seconds": float(light_time),
                }
            )
    finally:
        spice.kclear()
    data_path = OUTPUT / "lro_spice_positions_20170915.csv"
    with data_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "dataset_id": "lro_spice",
        "product_id": "LRO-L-SPICE-6-V1.0",
        "source_urls": [
            "https://naif.jpl.nasa.gov/naif/data_archived.html",
            "https://naif.jpl.nasa.gov/pub/naif/pds/data/lro-l-spice-6-v1.0/lrosp_1000/",
        ],
        "kernel_files": [SPK_NAME, LSK_NAME],
        "selection": "Hourly epochs on 2017-09-15 UTC, 24 records.",
        "time_coverage": {
            "start_utc": rows[0]["timestamp_utc"],
            "stop_utc": rows[-1]["timestamp_utc"],
        },
        "reference_frame": "J2000",
        "observer": "MOON (NAIF ID 301)",
        "target": "LRO spacecraft (NAIF ID -85)",
        "position_units": "km",
        "derived_fields": ["distance_from_moon_center_km", "one_way_light_time_seconds"],
        "transformations": [
            "SPICE ET converted to UTC using naif0012.tls.",
            "spkpos computed LRO position relative to the Moon in J2000.",
            "Distance calculated from the three Cartesian position components.",
            "No interpolation, imputation, or fabricated measurements.",
        ],
        "source_sha256": sha256(RAW / SPK_NAME),
        "processed_csv_sha256": sha256(data_path),
        "record_count": len(rows),
    }
    (OUTPUT / "lro_spice_processing_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "record_count": len(rows),
        "position_component_units": "km",
        "distance_from_moon_center_km": {
            "minimum": min(row["distance_from_moon_center_km"] for row in rows),
            "maximum": max(row["distance_from_moon_center_km"] for row in rows),
        },
    }
    (OUTPUT / "lro_spice_summary_statistics.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
