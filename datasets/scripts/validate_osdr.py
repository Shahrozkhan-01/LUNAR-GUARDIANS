"""Validate the public OSD-53 files without inspecting restricted data."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datasets" / "raw" / "astronaut_health" / "osdr"
REPORT = ROOT / "datasets" / "validation_reports" / "osdr_validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    expected = [
        "GLDS-53_microarray_E-GEOD-47126.processed.zip",
        "GLDS-53_microarray_E-GEOD-47126.additional.zip",
        "OSD-53_metadata_OSD-53-ISA.zip",
        "OSD-53_study_metadata.json",
        "OSD-53_file_metadata.json",
    ]
    files = []
    archive_members = {}
    for name in expected:
        path = RAW / name
        files.append(
            {
                "name": name,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": sha256(path) if path.is_file() else None,
            }
        )
        if path.suffix == ".zip" and path.is_file():
            with ZipFile(path) as archive:
                archive_members[name] = archive.namelist()
    passed = all(item["exists"] and item["size_bytes"] > 0 for item in files)
    passed = passed and len(
        [member for member in archive_members.get(expected[0], []) if "sample_table" in member]
    ) == 13
    passed = passed and "GSE47126_Fold_change_data.txt" in archive_members.get(expected[1], [])
    report = {
        "dataset_id": "OSD-53",
        "genelab_id": "GLDS-53",
        "validation_status": "PASS" if passed else "FAIL",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-53",
        "api_url": "https://osdr.nasa.gov/geode-py/ws/repo/studies/OSD-53",
        "sample_count": 13,
        "organism": "Homo sapiens",
        "checks": files,
        "archive_members": archive_members,
        "warnings": [
            "Original raw microarray data are unavailable according to the study record.",
            "Only public processed and metadata files were downloaded.",
            "No individual identities are exposed or inferred.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
