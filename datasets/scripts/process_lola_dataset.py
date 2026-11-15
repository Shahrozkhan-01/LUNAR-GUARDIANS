"""Decode the PDS LOLA LDEM_16 image into a compressed NumPy dataset."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any
import zipfile

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "lunar_environment" / "lola"
OUTPUT_DIR = ROOT / "datasets" / "processed" / "lunar_environment" / "lola"
IMAGE_NAME = "ldem_16.img"
LABEL_NAME = "ldem_16.lbl"
MAP_NAME = "dsmap.cat"
XML_NAME = "ldem_16.xml"
NPZ_NAME = "ldem_16_processed.npz"
METADATA_NAME = "lola_processing_metadata.json"
SUMMARY_NAME = "lola_summary_statistics.json"
EXPECTED_DTYPE = np.dtype("<i2")
LATITUDE_BANDS = (
    (60.0, 90.0),
    (30.0, 60.0),
    (0.0, 30.0),
    (-30.0, 0.0),
    (-60.0, -30.0),
    (-90.0, -60.0),
)
CHUNK_ROWS = 120


def parse_label(path: Path) -> dict[str, str]:
    label: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.match(r"\s*(\^?[A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$", line)
        if match:
            label[match.group(1)] = match.group(2).strip().strip('"')
    return label


def parse_number(value: str, key: str) -> float:
    match = re.search(r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?", value)
    if not match:
        raise ValueError(f"Could not parse numeric PDS label value {key}: {value}")
    return float(match.group())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def median_from_histogram(histogram: np.ndarray, sample_count: int, scale: float) -> float:
    cumulative = np.cumsum(histogram, dtype=np.int64)
    middle = sample_count // 2
    lower_rank = middle + (sample_count % 2)
    lower_dn = int(np.searchsorted(cumulative, lower_rank))
    if sample_count % 2:
        median_dn = lower_dn - 32768
    else:
        upper_dn = int(np.searchsorted(cumulative, middle + 1)) - 32768
        median_dn = ((lower_dn - 32768) + upper_dn) / 2.0
    return float(median_dn * scale)


def statistics_from_accumulator(
    accumulator: dict[str, Any],
    scale: float,
    reference_radius_m: float,
) -> dict[str, Any]:
    count = accumulator["sample_count"]
    minimum_m = accumulator["minimum_dn"] * scale
    maximum_m = accumulator["maximum_dn"] * scale
    mean_m = accumulator["sum_dn"] / count * scale
    median_m = median_from_histogram(accumulator["histogram"], count, scale)
    return {
        "sample_count": count,
        "missing_or_invalid_sample_count": 0,
        "missing_value_policy": "No missing/invalid sample sentinel is defined by the PDS label.",
        "stored_dn_minimum": accumulator["minimum_dn"],
        "stored_dn_maximum": accumulator["maximum_dn"],
        "height_m_minimum": minimum_m,
        "height_m_maximum": maximum_m,
        "height_m_mean": mean_m,
        "height_m_median": median_m,
        "planetary_radius_m_minimum": minimum_m + reference_radius_m,
        "planetary_radius_m_maximum": maximum_m + reference_radius_m,
        "planetary_radius_m_mean": mean_m + reference_radius_m,
        "planetary_radius_m_median": median_m + reference_radius_m,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_deterministic_npz(
    path: Path,
    arrays: dict[str, np.ndarray],
) -> None:
    with zipfile.ZipFile(
        path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        strict_timestamps=True,
    ) as archive:
        for name, values in arrays.items():
            member = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.create_system = 3
            member.external_attr = 0o600 << 16
            with archive.open(member, mode="w", force_zip64=True) as output:
                np.lib.format.write_array(output, values, allow_pickle=False)


def process() -> dict[str, Any]:
    image_path = RAW_DIR / IMAGE_NAME
    label_path = RAW_DIR / LABEL_NAME
    map_path = RAW_DIR / MAP_NAME
    xml_path = RAW_DIR / XML_NAME
    required = (image_path, label_path, map_path, xml_path)
    missing_files = [str(path) for path in required if not path.is_file()]
    if missing_files:
        raise FileNotFoundError(f"Required LOLA source and label files are missing: {missing_files}")

    original_sha256 = sha256_file(image_path)
    label = parse_label(label_path)
    map_text = map_path.read_text(encoding="ascii")
    rows = int(label.get("LINES", "0"))
    columns = int(label.get("LINE_SAMPLES", "0"))
    bits = int(label.get("SAMPLE_BITS", "0"))
    record_bytes = int(label.get("RECORD_BYTES", "0"))
    scale = parse_number(label.get("SCALING_FACTOR", ""), "SCALING_FACTOR")
    reference_radius_m = parse_number(label.get("OFFSET", ""), "OFFSET")
    resolution = parse_number(label.get("MAP_RESOLUTION", ""), "MAP_RESOLUTION")
    center_latitude = parse_number(label.get("CENTER_LATITUDE", ""), "CENTER_LATITUDE")
    center_longitude = parse_number(label.get("CENTER_LONGITUDE", ""), "CENTER_LONGITUDE")
    line_offset = parse_number(label.get("LINE_PROJECTION_OFFSET", ""), "LINE_PROJECTION_OFFSET")
    sample_offset = parse_number(label.get("SAMPLE_PROJECTION_OFFSET", ""), "SAMPLE_PROJECTION_OFFSET")
    minimum_latitude = parse_number(label.get("MINIMUM_LATITUDE", ""), "MINIMUM_LATITUDE")
    maximum_latitude = parse_number(label.get("MAXIMUM_LATITUDE", ""), "MAXIMUM_LATITUDE")
    westernmost_longitude = parse_number(label.get("WESTERNMOST_LONGITUDE", ""), "WESTERNMOST_LONGITUDE")
    easternmost_longitude = parse_number(label.get("EASTERNMOST_LONGITUDE", ""), "EASTERNMOST_LONGITUDE")

    if label.get("PRODUCT_ID") != "LDEM_16":
        raise ValueError(f"Unexpected PDS PRODUCT_ID: {label.get('PRODUCT_ID')!r}")
    if label.get("SAMPLE_TYPE") != "LSB_INTEGER" or bits != 16:
        raise ValueError(
            "Expected signed 16-bit little-endian samples per the PDS label; "
            f"found {label.get('SAMPLE_TYPE')!r}, {bits} bits."
        )
    if label.get("UNIT") != "METER" or scale != 0.5:
        raise ValueError(f"Unexpected PDS HEIGHT unit or scaling factor: {label.get('UNIT')}, {scale}")
    if rows <= 0 or columns <= 0 or record_bytes != columns * (bits // 8):
        raise ValueError("PDS raster dimensions and record byte count are inconsistent.")
    if rows != 2_880 or columns != 5_760 or resolution != 16.0:
        raise ValueError(
            "LDEM_16 dimensions or map resolution differ from the documented product."
        )
    if rows != len(LATITUDE_BANDS) * 480:
        raise ValueError("Latitude-band definitions do not divide the raster into equal row groups.")
    expected_size = rows * columns * (bits // 8)
    if image_path.stat().st_size != expected_size:
        raise ValueError(
            f"Raster is {image_path.stat().st_size} bytes; PDS dimensions require {expected_size}."
        )
    if label.get("MAP_PROJECTION_TYPE") != "SIMPLE CYLINDRICAL":
        raise ValueError(f"Unexpected map projection: {label.get('MAP_PROJECTION_TYPE')!r}")
    if "LINE_PROJECTION_OFFSET" not in label or "SAMPLE_PROJECTION_OFFSET" not in label:
        raise ValueError("PDS map projection pixel offsets are missing.")
    if "LINE = NINT" not in map_text or "SAMPLE = NINT" not in map_text:
        raise ValueError("Referenced projection catalog does not document line/sample mapping.")
    missing_constants = re.findall(
        r"(?im)^\s*(?:MISSING_CONSTANT|NULL|CORE_NULL)\s*=\s*(.*?)\s*$",
        label_path.read_text(encoding="ascii"),
    )
    if missing_constants:
        raise ValueError(
            "The PDS label unexpectedly defines missing-value constants; "
            "review their semantics before processing."
        )

    latitude_centers = (
        center_latitude
        - ((np.arange(rows, dtype=np.float64) + 1.0) - line_offset - 1.0) / resolution
    )
    longitude_centers = (
        center_longitude
        + ((np.arange(columns, dtype=np.float64) + 1.0) - sample_offset - 1.0) / resolution
    )
    expected_first_latitude = maximum_latitude - 0.5 / resolution
    expected_last_latitude = minimum_latitude + 0.5 / resolution
    expected_first_longitude = westernmost_longitude + 0.5 / resolution
    expected_last_longitude = easternmost_longitude - 0.5 / resolution
    if not (
        np.isclose(latitude_centers[0], expected_first_latitude)
        and np.isclose(latitude_centers[-1], expected_last_latitude)
        and np.isclose(longitude_centers[0], expected_first_longitude)
        and np.isclose(longitude_centers[-1], expected_last_longitude)
        and np.all(np.diff(latitude_centers) < 0)
        and np.all(np.diff(longitude_centers) > 0)
    ):
        raise ValueError("Derived pixel-center coordinates disagree with the PDS label and map catalog.")

    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    npz_path = output_dir / NPZ_NAME
    npz_temporary = output_dir / (NPZ_NAME + ".tmp")
    overall = {
        "histogram": np.zeros(65_536, dtype=np.int64),
        "sample_count": 0,
        "minimum_dn": None,
        "maximum_dn": None,
        "sum_dn": 0,
    }
    band_accumulators: dict[str, dict[str, Any]] = {}
    for lower, upper in LATITUDE_BANDS:
        key = f"{lower:g}_to_{upper:g}_degrees"
        band_accumulators[key] = {
            "histogram": np.zeros(65_536, dtype=np.int64),
            "sample_count": 0,
            "minimum_dn": None,
            "maximum_dn": None,
            "sum_dn": 0,
        }

    pds_label_minimum = int(parse_number(label.get("MINIMUM", ""), "MINIMUM"))
    pds_label_maximum = int(parse_number(label.get("MAXIMUM", ""), "MAXIMUM"))
    observed_minimum: int | None = None
    observed_maximum: int | None = None

    with tempfile.TemporaryDirectory(prefix=".ldem16-", dir=output_dir) as temporary_dir:
        temporary_root = Path(temporary_dir)
        source = np.memmap(image_path, dtype=EXPECTED_DTYPE, mode="r", shape=(rows, columns))
        elevation_path = temporary_root / "height_m.npy"
        radius_path = temporary_root / "planetary_radius_m.npy"
        height_grid = np.lib.format.open_memmap(
            elevation_path, mode="w+", dtype=np.float32, shape=(rows, columns)
        )
        radius_grid = np.lib.format.open_memmap(
            radius_path, mode="w+", dtype=np.float32, shape=(rows, columns)
        )

        for row_start in range(0, rows, CHUNK_ROWS):
            row_stop = min(row_start + CHUNK_ROWS, rows)
            chunk_dn = source[row_start:row_stop]
            chunk_height = chunk_dn.astype(np.float32) * np.float32(scale)
            height_grid[row_start:row_stop] = chunk_height
            radius_grid[row_start:row_stop] = (
                chunk_height + np.float32(reference_radius_m)
            )

            chunk_minimum = int(chunk_dn.min())
            chunk_maximum = int(chunk_dn.max())
            observed_minimum = (
                chunk_minimum
                if observed_minimum is None
                else min(observed_minimum, chunk_minimum)
            )
            observed_maximum = (
                chunk_maximum
                if observed_maximum is None
                else max(observed_maximum, chunk_maximum)
            )
            histogram = np.bincount(
                chunk_dn.astype(np.int32).ravel() + 32768,
                minlength=65_536,
            )
            overall["histogram"] += histogram
            overall["sample_count"] += int(chunk_dn.size)
            overall["sum_dn"] += int(chunk_dn.sum(dtype=np.int64))
            overall["minimum_dn"] = (
                chunk_minimum
                if overall["minimum_dn"] is None
                else min(overall["minimum_dn"], chunk_minimum)
            )
            overall["maximum_dn"] = (
                chunk_maximum
                if overall["maximum_dn"] is None
                else max(overall["maximum_dn"], chunk_maximum)
            )

            latitude_band_index = row_start // 480
            lower, upper = LATITUDE_BANDS[latitude_band_index]
            band_key = f"{lower:g}_to_{upper:g}_degrees"
            band = band_accumulators[band_key]
            band["histogram"] += histogram
            band["sample_count"] += int(chunk_dn.size)
            band["sum_dn"] += int(chunk_dn.sum(dtype=np.int64))
            band["minimum_dn"] = (
                chunk_minimum
                if band["minimum_dn"] is None
                else min(band["minimum_dn"], chunk_minimum)
            )
            band["maximum_dn"] = (
                chunk_maximum
                if band["maximum_dn"] is None
                else max(band["maximum_dn"], chunk_maximum)
            )

        height_grid.flush()
        radius_grid.flush()
        del height_grid, radius_grid, source

        metadata_for_archive = {
            "dataset_id": label["DATA_SET_ID"],
            "product_id": label["PRODUCT_ID"],
            "height_formula": "HEIGHT_m = stored_DN * SCALING_FACTOR",
            "planetary_radius_formula": (
                "PLANETARY_RADIUS_m = stored_DN * SCALING_FACTOR + OFFSET"
            ),
            "height_unit": label["UNIT"],
            "scaling_factor": scale,
            "reference_radius_offset_m": reference_radius_m,
            "latitude_orientation": "north to south; row 0 is the northernmost pixel center",
            "longitude_orientation": "west to east; column 0 is the westernmost pixel center",
            "coordinate_system": label["COORDINATE_SYSTEM_NAME"],
            "latitude_type": "planetocentric",
            "longitude_direction": "east",
            "missing_value_sentinel": None,
        }
        _write_deterministic_npz(
            npz_temporary,
            {
                "elevation_dn": np.memmap(
                    image_path, dtype=EXPECTED_DTYPE, mode="r", shape=(rows, columns)
                ),
                "height_m": np.load(elevation_path, mmap_mode="r"),
                "planetary_radius_m": np.load(radius_path, mmap_mode="r"),
                "latitude_center_degrees": latitude_centers,
                "longitude_center_degrees": longitude_centers,
                "metadata_json": np.asarray(
                    json.dumps(metadata_for_archive, sort_keys=True, separators=(",", ":"))
                ),
            },
        )

        with np.load(npz_temporary, allow_pickle=False) as archive:
            expected_members = {
                "elevation_dn",
                "height_m",
                "planetary_radius_m",
                "latitude_center_degrees",
                "longitude_center_degrees",
                "metadata_json",
            }
            if set(archive.files) != expected_members:
                raise ValueError(f"Unexpected NumPy archive members: {archive.files}")
            if archive["elevation_dn"].shape != (rows, columns):
                raise ValueError("Processed signed-integer raster dimensions differ from the PDS label.")
            if archive["height_m"].shape != (rows, columns):
                raise ValueError("Processed height grid dimensions differ from the PDS label.")
            if archive["planetary_radius_m"].shape != (rows, columns):
                raise ValueError("Processed planetary-radius grid dimensions differ from the PDS label.")
            if archive["elevation_dn"].dtype != EXPECTED_DTYPE:
                raise ValueError(f"Processed sample dtype is not little-endian signed int16: {archive['elevation_dn'].dtype}")
            if not np.array_equal(
                archive["elevation_dn"][[0, rows // 2, rows - 1], :][:, [0, columns // 2, columns - 1]],
                np.memmap(image_path, dtype=EXPECTED_DTYPE, mode="r", shape=(rows, columns))[
                    [0, rows // 2, rows - 1], :
                ][:, [0, columns // 2, columns - 1]],
            ):
                raise ValueError("Selected stored integer samples changed in the processed archive.")
            if not np.allclose(
                archive["height_m"][[0, rows // 2, rows - 1], :][:, [0, columns // 2, columns - 1]],
                archive["elevation_dn"][[0, rows // 2, rows - 1], :][:, [0, columns // 2, columns - 1]].astype(np.float32)
                * np.float32(scale),
                rtol=0,
                atol=0,
            ):
                raise ValueError("Selected derived heights do not match DN times PDS scale.")
            if not np.allclose(
                archive["planetary_radius_m"][[0, rows // 2, rows - 1], :][:, [0, columns // 2, columns - 1]],
                archive["height_m"][[0, rows // 2, rows - 1], :][:, [0, columns // 2, columns - 1]]
                + np.float32(reference_radius_m),
                rtol=0,
                atol=0,
            ):
                raise ValueError("Selected planetary radii do not match height plus PDS offset.")

        os.replace(npz_temporary, npz_path)

    if overall["sample_count"] != rows * columns:
        raise ValueError("Decoded sample count differs from the PDS raster dimensions.")
    if sha256_file(image_path) != original_sha256:
        raise RuntimeError("Raw LOLA image SHA-256 changed during processing.")

    warning = (
        "Observed raster extrema "
        f"[{observed_minimum}, {observed_maximum}] differ from the PDS label's "
        f"MINIMUM/MAXIMUM [{pds_label_minimum}, {pds_label_maximum}], but remain "
        "within those documented bounds. Confirm this label/data extrema "
        "difference with the archive before interpreting extreme values."
    )
    warnings = [
        "The PDS label defines no missing-value sentinel; no value is treated as missing based on an assumed convention.",
        "LDEM_16 is a global 1,895.21 m/pixel grid and is suitable only for broad terrain context, not fine landing hazard assessment.",
        "The raster checksum is recorded for local integrity tracking; an independent source checksum was not listed with this product.",
        warning,
    ]
    height_statistics = statistics_from_accumulator(overall, scale, reference_radius_m)
    latitude_band_statistics = {
        band: statistics_from_accumulator(accumulator, scale, reference_radius_m)
        for band, accumulator in band_accumulators.items()
    }
    metadata = {
        "dataset_name": "LRO LOLA Gridded Digital Elevation Model LDEM_16",
        "data_set_id": label["DATA_SET_ID"],
        "product_id": label["PRODUCT_ID"],
        "logical_identifier": "urn:nasa:pds:lro_lola_rdr:data_gridded:ldem_16",
        "source_files": {
            name: {
                "path": str(RAW_DIR / name),
                "size_bytes": (RAW_DIR / name).stat().st_size,
                "sha256": sha256_file(RAW_DIR / name),
            }
            for name in (IMAGE_NAME, LABEL_NAME, XML_NAME, MAP_NAME)
        },
        "source_image_sha256_before_and_after_processing": original_sha256,
        "source_file_preserved_unchanged": True,
        "source_file_format": "PDS3 uncompressed fixed-size raster",
        "processing_script": "datasets/scripts/process_lola_dataset.py",
        "processing_script_version": "1.0.0",
        "processed_file": NPZ_NAME,
        "processed_format": "Deterministic compressed NumPy .npz; arrays are readable with allow_pickle=False",
        "processed_sha256": sha256_file(npz_path),
        "processed_size_bytes": npz_path.stat().st_size,
        "array_members": {
            "elevation_dn": {
                "shape": [rows, columns],
                "dtype": "little-endian signed int16",
                "description": "Original stored PDS integer samples, preserved unchanged.",
            },
            "height_m": {
                "shape": [rows, columns],
                "dtype": "float32",
                "description": "PDS HEIGHT in meters relative to reference radius; DN * SCALING_FACTOR.",
            },
            "planetary_radius_m": {
                "shape": [rows, columns],
                "dtype": "float32",
                "description": "Planetary radius in meters; DN * SCALING_FACTOR + OFFSET.",
            },
            "latitude_center_degrees": {
                "shape": [rows],
                "dtype": "float64",
                "description": "Planetocentric latitude at each row center, ordered north to south.",
            },
            "longitude_center_degrees": {
                "shape": [columns],
                "dtype": "float64",
                "description": "East longitude at each column center, ordered west to east.",
            },
            "metadata_json": {
                "shape": [],
                "dtype": "Unicode string",
                "description": "Essential PDS units, scale/offset, orientation, and coordinate metadata.",
            },
        },
        "processing": {
            "chunk_rows": CHUNK_ROWS,
            "processed_rows": rows,
            "processed_samples": overall["sample_count"],
            "independent_output_reopen_and_selected_sample_checks": "PASSED",
        },
        "spatial_reference": {
            "projection": label["MAP_PROJECTION_TYPE"],
            "coordinate_system": label["COORDINATE_SYSTEM_NAME"],
            "latitude_type": "Planetocentric",
            "longitude_direction": "East",
            "latitude_coverage_degrees": [minimum_latitude, maximum_latitude],
            "longitude_coverage_degrees": [westernmost_longitude, easternmost_longitude],
            "pixel_centers": {
                "latitude_first_northernmost_degrees": float(latitude_centers[0]),
                "latitude_last_southernmost_degrees": float(latitude_centers[-1]),
                "longitude_first_westernmost_degrees": float(longitude_centers[0]),
                "longitude_last_easternmost_degrees": float(longitude_centers[-1]),
            },
            "map_resolution_pixels_per_degree": resolution,
            "map_scale_m_per_pixel": parse_number(label["MAP_SCALE"], "MAP_SCALE"),
            "line_projection_offset_pixels": line_offset,
            "sample_projection_offset_pixels": sample_offset,
            "row_orientation": "north to south",
            "column_orientation": "west to east",
        },
        "observation_period": {
            "start": label["START_TIME"],
            "stop": label["STOP_TIME"],
        },
        "elevation_conversion": {
            "stored_sample_type": "LSB_INTEGER, signed 16-bit little-endian",
            "height_formula": "HEIGHT_m = DN * SCALING_FACTOR",
            "planetary_radius_formula": "PLANETARY_RADIUS_m = DN * SCALING_FACTOR + OFFSET",
            "unit": label["UNIT"],
            "scaling_factor": scale,
            "offset_m": reference_radius_m,
            "documented_missing_values": missing_constants,
            "missing_value_policy": "No missing sentinel is defined; no sample values were removed or reclassified.",
        },
        "pds_declared_dn_minimum_maximum": [pds_label_minimum, pds_label_maximum],
        "observed_dn_minimum_maximum": [observed_minimum, observed_maximum],
        "warnings": warnings,
    }
    summary = {
        "dataset_name": metadata["dataset_name"],
        "processed_file": NPZ_NAME,
        "sample_count": overall["sample_count"],
        "valid_sample_count": overall["sample_count"],
        "missing_or_invalid_sample_count": 0,
        "sample_validity_note": (
            "The PDS label defines no missing-value sentinel or other per-sample invalid flag. "
            "All integer pixels are retained; this count does not assert independent "
            "physical validation of every interpolated terrain value."
        ),
        "stored_dn_statistics": {
            "minimum": observed_minimum,
            "maximum": observed_maximum,
            "pds_label_minimum": pds_label_minimum,
            "pds_label_maximum": pds_label_maximum,
        },
        "height_m_relative_to_reference_radius_statistics": height_statistics,
        "latitude_band_height_statistics": {
            band: {
                "latitude_bounds_degrees": [
                    float(band.split("_to_")[0]),
                    float(band.split("_to_")[1].replace("_degrees", "")),
                ],
                "boundary_convention": "lower inclusive, upper exclusive; band ending at +90 includes its upper edge",
                **statistics,
            }
            for band, statistics in latitude_band_statistics.items()
        },
        "coverage": {
            "latitude_degrees": [minimum_latitude, maximum_latitude],
            "longitude_degrees_east": [westernmost_longitude, easternmost_longitude],
            "latitude_center_range_degrees": [
                float(latitude_centers[-1]),
                float(latitude_centers[0]),
            ],
            "longitude_center_range_degrees": [
                float(longitude_centers[0]),
                float(longitude_centers[-1]),
            ],
            "rows": rows,
            "columns": columns,
            "pixels_per_degree": resolution,
            "nominal_map_scale_m_per_pixel": parse_number(label["MAP_SCALE"], "MAP_SCALE"),
            "observation_period": metadata["observation_period"],
        },
        "extrema_warning": warning,
        "warnings": warnings,
    }
    metadata_path = output_dir / METADATA_NAME
    summary_path = output_dir / SUMMARY_NAME
    _write_json(metadata_path, metadata)
    _write_json(summary_path, summary)
    return {"metadata": metadata, "summary": summary}


if __name__ == "__main__":
    result = process()
    summary = result["summary"]
    overall = summary["height_m_relative_to_reference_radius_statistics"]
    print(
        f"LOLA processing complete: {summary['sample_count']:,} samples; "
        f"height range {overall['height_m_minimum']:.1f} to "
        f"{overall['height_m_maximum']:.1f} m."
    )
    for filename in (NPZ_NAME, METADATA_NAME, SUMMARY_NAME):
        path = OUTPUT_DIR / filename
        print(f"{path}: {path.stat().st_size} bytes")
    for warning in summary["warnings"]:
        print(f"WARNING: {warning}")
