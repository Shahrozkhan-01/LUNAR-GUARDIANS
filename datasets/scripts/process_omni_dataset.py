"""Create a bounded, lossless CSV view of the NASA OMNI2 hourly source."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from omni_common import FIELDS, iter_records

ROOT = SCRIPT_DIR.parents[1]
SOURCE = ROOT / "datasets/raw/space_weather/omni/omni2_2020.dat"
OUTPUT = ROOT / "datasets/processed/space_weather/omni"
START = datetime(2020, 1, 1, tzinfo=timezone.utc)
END = datetime(2020, 2, 1, tzinfo=timezone.utc)

UNIT_BY_NAME = {
    name: unit for name, unit in {
        "imf_magnitude_nt": "nT", "field_vector_magnitude_nt": "nT",
        "bx_gse_nt": "nT", "by_gse_nt": "nT", "bz_gse_nt": "nT",
        "by_gsm_nt": "nT", "bz_gsm_nt": "nT", "proton_density_cm3": "cm^-3",
        "solar_wind_speed_km_s": "km/s", "proton_temperature_k": "K",
        "flow_pressure_npa": "nPa", "electric_field_mv_m": "mV/m",
        "plasma_beta": "dimensionless", "alfven_mach_number": "dimensionless",
        "magnetosonic_mach_number": "dimensionless",
    }.items()
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    records = [
        record for _, record in iter_records(SOURCE)
        if START <= datetime.fromisoformat(record["timestamp_utc"].replace("Z", "+00:00")) < END
    ]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data_path = OUTPUT / "omni_hourly_20200101_20200201.csv"
    fieldnames = ["timestamp_utc"] + [name for name, _ in FIELDS]
    with data_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({name: record[name] for name in fieldnames} for record in records)

    summary = {
        "dataset_id": "omni_hourly",
        "record_count": len(records),
        "time_coverage": {"start_utc": records[0]["timestamp_utc"], "end_utc": records[-1]["timestamp_utc"]},
        "variables": [name for name, _ in FIELDS],
        "validity": "Official OMNI fill values remain in the CSV; missing counts are in the validation report.",
        "source_sha256": sha256(SOURCE),
        "processed_csv_sha256": sha256(data_path),
        "transformation": "Selected records whose UTC timestamp is 2020-01-01 inclusive through 2020-02-01 exclusive; no scientific values were rescaled or imputed.",
    }
    (OUTPUT / "omni_summary_statistics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "dataset_id": "omni_hourly",
        "product": "OMNI2_2020.DAT hourly means",
        "source_url": "https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_2020.dat",
        "documentation_url": "https://omniweb.gsfc.nasa.gov/html/ow_data.html",
        "source_format": "ASCII fixed-width OMNI2 record, parsed by whitespace into 53 official fields",
        "selection": {"start_utc_inclusive": "2020-01-01T00:00:00Z", "end_utc_exclusive": "2020-02-01T00:00:00Z"},
        "variables": {
            name: {"type": converter.__name__, "units": UNIT_BY_NAME.get(name, "See official omni2.text")}
            for name, converter in FIELDS
        },
        "processed_output": data_path.name,
        "source_sha256": summary["source_sha256"],
        "processed_csv_sha256": summary["processed_csv_sha256"],
        "limitations": [
            "OMNI is a merged, time-shifted near-Earth dataset, not a lunar-surface measurement.",
            "No field is an astronaut radiation dose measurement and no dose conversion is performed.",
        ],
    }
    (OUTPUT / "omni_processing_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(data_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
