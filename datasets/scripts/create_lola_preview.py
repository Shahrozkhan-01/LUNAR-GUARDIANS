"""Create a compact, deterministic sample of the processed LOLA LDEM_16 grid."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "lunar_environment"
    / "lola"
    / "ldem_16_processed.npz"
)
OUTPUT_DIRECTORY = SOURCE_FILE.parent
PREVIEW_FILE = OUTPUT_DIRECTORY / "ldem_16_preview.csv"
METADATA_FILE = OUTPUT_DIRECTORY / "ldem_16_preview_metadata.json"
SAMPLE_STRIDE_PIXELS = 16
HEIGHT_SCALE_METERS = 0.5
REFERENCE_RADIUS_METERS = 1_737_400


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_preview(source_file: Path, preview_file: Path, metadata_file: Path) -> None:
    with np.load(source_file, allow_pickle=False) as archive:
        elevation = archive["elevation_dn"]
        latitudes = archive["latitude_center_degrees"]
        longitudes = archive["longitude_center_degrees"]

        if elevation.ndim != 2 or elevation.shape != (len(latitudes), len(longitudes)):
            raise ValueError("LOLA array dimensions do not match its coordinate axes.")

        sampled_rows = list(range(0, elevation.shape[0], SAMPLE_STRIDE_PIXELS))
        sampled_columns = list(range(0, elevation.shape[1], SAMPLE_STRIDE_PIXELS))
        preview_file.parent.mkdir(parents=True, exist_ok=True)

        with preview_file.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(
                (
                    "latitude_center_degrees",
                    "longitude_center_degrees",
                    "elevation_dn",
                    "height_m",
                    "planetary_radius_m",
                )
            )
            for row in sampled_rows:
                latitude = float(latitudes[row])
                for column in sampled_columns:
                    elevation_dn = int(elevation[row, column])
                    height_m = elevation_dn * HEIGHT_SCALE_METERS
                    radius_m = height_m + REFERENCE_RADIUS_METERS
                    writer.writerow(
                        (
                            f"{latitude:.8f}",
                            f"{float(longitudes[column]):.8f}",
                            elevation_dn,
                            f"{height_m:.1f}",
                            f"{radius_m:.1f}",
                        )
                    )

    record_count = len(sampled_rows) * len(sampled_columns)
    preview_metadata = {
        "source_file": "ldem_16_processed.npz",
        "source_sha256": _sha256(source_file),
        "preview_file": preview_file.name,
        "preview_sha256": _sha256(preview_file),
        "record_count": record_count,
        "grid_shape": [len(sampled_rows), len(sampled_columns)],
        "sampling_method": (
            "Select every 16th original row and column; no interpolation or "
            "aggregation is applied."
        ),
        "source_pixels_per_degree": 16,
        "sample_stride_pixels": SAMPLE_STRIDE_PIXELS,
        "nominal_spacing_at_equator_km": 30.32336,
        "coordinate_reference": (
            "PDS MEAN EARTH/POLAR AXIS OF DE421; planetocentric latitude; "
            "east-positive longitude; pixel centers."
        ),
        "elevation_dn_definition": "Original signed integer sample from LDEM_16.",
        "height_m_definition": "elevation_dn * 0.5; derived relative to the product reference radius.",
        "planetary_radius_m_definition": "height_m + 1,737,400 m; derived.",
        "limitations": [
            "This is a regular sample of the global source grid, not the full-resolution grid.",
            "The sample spacing is about 30.3 km at the equator and varies with latitude.",
            "It is not suitable for local landing hazards, slope analysis, or site-safety conclusions.",
            "Full-grid summary statistics describe the source raster, not just this preview.",
        ],
    }
    metadata_file.write_text(
        json.dumps(preview_metadata, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_FILE)
    parser.add_argument("--preview", type=Path, default=PREVIEW_FILE)
    parser.add_argument("--metadata", type=Path, default=METADATA_FILE)
    arguments = parser.parse_args()
    create_preview(arguments.source, arguments.preview, arguments.metadata)
    print(f"Created {arguments.preview}")
    print(f"Created {arguments.metadata}")


if __name__ == "__main__":
    main()
