"""Validate the bounded official LRO SPICE sample."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datasets" / "raw" / "communication_navigation" / "lro_spice"
SPK = RAW / "lrorg_2017258_2017349_v01.bsp"
LABEL = RAW / "lrorg_2017258_2017349_v01.lbl"
LSK = RAW / "naif0012.tls"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    checks = []
    for path in (SPK, LABEL, LSK):
        checks.append(
            {
                "file": path.name,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": sha256(path) if path.is_file() else None,
            }
        )
    label_text = LABEL.read_text(encoding="ascii") if LABEL.is_file() else ""
    passed = all(item["exists"] and item["size_bytes"] > 0 for item in checks)
    passed = passed and 'DATA_SET_ID' in label_text and 'LRO-L-SPICE-6-V1.0' in label_text
    passed = passed and 'START_TIME' in label_text and '2017-09-15T00:00:00' in label_text
    passed = passed and 'STOP_TIME' in label_text and '2017-12-15T00:00:00' in label_text
    report = {
        "dataset_id": "lro-l-spice-6-v1.0",
        "validation_status": "PASS" if passed else "FAIL",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "https://naif.jpl.nasa.gov/pub/naif/pds/data/lro-l-spice-6-v1.0/lrosp_1000/",
        "coverage": {
            "start_utc": "2017-09-15T00:00:00Z",
            "stop_utc": "2017-12-15T00:00:00Z",
        },
        "coordinate_frame": "J2000",
        "position_reference": "MOON",
        "position_units": "km",
        "checks": checks,
        "warnings": [
            "SPICE positions are computed geometry from kernels, not direct telemetry.",
            "The archive label describes a reconstructed definitive LRO trajectory.",
        ],
    }
    output = ROOT / "datasets" / "validation_reports" / "lro_spice_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
