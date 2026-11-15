"""Process official LEND DLD/DLX binary records without scientific imputation."""

from __future__ import annotations

import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from lend_common import load_records, write_csv


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datasets" / "raw" / "lunar_environment" / "lend"
OUT = ROOT / "datasets" / "processed" / "lunar_environment" / "lend"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    records = load_records(RAW)
    csv_path = OUT / "lend_20200101_processed.csv"
    write_csv(records, csv_path)
    measurement_fields = [key for key in records[0] if key.endswith(("counts", "sigma_counts"))]
    stats = {}
    for name in measurement_fields:
        values = [row[name] for row in records if isinstance(row[name], (int, float)) and row[name] >= 0]
        stats[name] = {
            "valid_count": len(values),
            "negative_source_value_count": sum(1 for row in records if isinstance(row[name], (int, float)) and row[name] < 0),
            "minimum": min(values) if values else None,
            "mean": statistics.fmean(values) if values else None,
            "maximum": max(values) if values else None,
        }
    metadata = {
        "dataset_id": "lro_lend_rdr_dld_dlx_20200101",
        "product_identifiers": [
            "urn:nasa:pds:lro_lend:data_science_derived:lend_rdr_dld_20200101",
            "urn:nasa:pds:lro_lend:data_science_derived:lend_rdr_dlx_20200101",
        ],
        "source_urls": [
            "https://pds-geosciences.wustl.edu/missions/lro/lend.htm",
            "https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/document/lend_rdr_sis.htm",
        ],
        "source_format": "PDS3 fixed-length big-endian binary tables with PDS4 labels",
        "record_count": len(records),
        "record_join": "DLD and DLX records joined by identical LRO_TIME and UTC at the same record index",
        "variables": {
            "timestamp_utc": {"units": "UTC", "description": "UTC midpoint timestamp from source record"},
            "lunarcentric_latitude_deg": {"units": "degree", "description": "Lunar-centric latitude"},
            "lunarcentric_east_longitude_deg": {"units": "degree", "description": "Lunar-centric east longitude"},
            "collection_duration_s": {"units": "s", "description": "Collection duration"},
            "detector_counts": {"units": "counts", "description": "DLD detector/background count fields; source values preserved"},
            "corrected_counts_sigma": {"units": "counts", "description": "DLX corrected-count uncertainty fields; negative values are source unusable markers"},
        },
        "missing_value_policy": "No imputation or silent deletion. Negative source-defined unusable corrected counts/sigma values remain in the processed CSV.",
        "transformations": [
            "Decoded big-endian fields using the official PDS labels.",
            "Joined the one-day DLD spatial/background/count record with the matching DLX corrected-count uncertainty record.",
            "Added a UTC Z suffix to the source UTC text.",
            "Did not convert counts to flux, dose, water-ice abundance, or any other derived quantity.",
        ],
        "source_sha256": {path.name: sha256(path) for path in RAW.glob("*") if path.is_file()},
        "processed_csv_sha256": sha256(csv_path),
        "processed_output_readback_verified": True,
    }
    (OUT / "lend_processing_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    summary = {
        "dataset_id": metadata["dataset_id"],
        "record_count": len(records),
        "time_coverage": {"start": records[0]["timestamp_utc"], "end": records[-1]["timestamp_utc"]},
        "spatial_coverage": {
            "latitude_min_deg": min(row["lunarcentric_latitude_deg"] for row in records),
            "latitude_max_deg": max(row["lunarcentric_latitude_deg"] for row in records),
            "east_longitude_min_deg": min(row["lunarcentric_east_longitude_deg"] for row in records),
            "east_longitude_max_deg": max(row["lunarcentric_east_longitude_deg"] for row in records),
        },
        "measurement_statistics": stats,
        "scientific_limitations": [
            "LEND is an orbital lunar neutron detector, not a surface detector.",
            "Counts and count uncertainties are not astronaut radiation dose.",
            "Neutron observations alone do not confirm water ice at a specific location.",
        ],
    }
    (OUT / "lend_summary_statistics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "csv": str(csv_path)}))


if __name__ == "__main__":
    main()
