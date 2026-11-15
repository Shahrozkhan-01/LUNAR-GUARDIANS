"""Read-only access to the project's processed NASA dataset products."""

import csv
from dataclasses import dataclass
import gzip
import json
import math
from pathlib import Path
from typing import Any, Dict, Optional
import zipfile

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASETS_ROOT = PROJECT_ROOT / "datasets"
CATALOG_PATH = DATASETS_ROOT / "metadata" / "dataset_catalog.csv"

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


class DatasetServiceError(RuntimeError):
    """A safe, user-facing dataset API error."""

    status_code = 503
    error_code = "dataset_unavailable"


class DatasetNotFoundError(DatasetServiceError):
    status_code = 404
    error_code = "dataset_not_found"


class DatasetRecordsNotAvailableError(DatasetServiceError):
    status_code = 409
    error_code = "records_not_available"


class DatasetUnavailableError(DatasetServiceError):
    status_code = 503
    error_code = "dataset_unavailable"


@dataclass(frozen=True)
class DatasetSpec:
    dataset_name: str
    processed_directory: str
    data_file: str
    metadata_file: str
    summary_file: str
    data_type: str
    scientific_limitations: tuple[str, ...]
    record_format: Optional[str] = None
    metadata_fields: tuple[str, ...] = ()
    preview_file: Optional[str] = None
    preview_metadata_file: Optional[str] = None


DATASET_SPECS: Dict[str, DatasetSpec] = {
    "diviner": DatasetSpec(
        dataset_name=(
            "LRO Diviner Global Cumulative Average Product: "
            "global_cumul_avg_cyl_80s70s_002"
        ),
        processed_directory="lunar_environment/diviner",
        data_file="global_cumul_avg_cyl_80s70s_002.csv.gz",
        metadata_file="diviner_processing_metadata.json",
        summary_file="diviner_summary_statistics.json",
        data_type="remote_sensing_observation",
        scientific_limitations=(
            "Historical brightness temperature is not live habitat, astronaut, or forecast temperature.",
            "This gridded product is historical context, not an in-situ temperature measurement.",
        ),
        metadata_fields=(
            "columns",
            "data_set_id",
            "missing_value_policy",
            "observation_period",
            "output_format",
            "processed_row_count",
            "processed_output_readback_verified",
            "product_id",
            "spatial_reference",
        ),
    ),
    "lola": DatasetSpec(
        dataset_name="LRO LOLA Gridded Digital Elevation Model (LDEM_16)",
        processed_directory="lunar_environment/lola",
        data_file="ldem_16_processed.npz",
        metadata_file="lola_processing_metadata.json",
        summary_file="lola_summary_statistics.json",
        data_type="derived_topographic_product",
        scientific_limitations=(
            "LDEM_16 is broad terrain context at approximately 1.9 km/pixel, not detailed landing-hazard information.",
            "The hosted record preview samples every 16th source row and column; it is not the full grid or suitable for local site assessment.",
            "The observed raster extrema differ from the PDS label extrema; the documented warning is retained.",
        ),
        record_format="lola_preview_csv",
        metadata_fields=(
            "array_members",
            "data_set_id",
            "elevation_conversion",
            "logical_identifier",
            "observation_period",
            "observed_dn_minimum_maximum",
            "pds_declared_dn_minimum_maximum",
            "product_id",
            "spatial_reference",
            "warnings",
        ),
        preview_file="ldem_16_preview.csv",
        preview_metadata_file="ldem_16_preview_metadata.json",
    ),
    "ace_epam": DatasetSpec(
        dataset_name="ACE EPAM energetic-particle observations",
        processed_directory="space_weather/ace_epam",
        data_file="ace_epam_20200101_processed.npz",
        metadata_file="ace_epam_processing_metadata.json",
        summary_file="ace_epam_summary_statistics.json",
        data_type="spacecraft_observation",
        scientific_limitations=(
            "ACE EPAM measurements are from the ACE spacecraft near Sun-Earth L1, not the lunar surface.",
            "ACE particle measurements are not astronaut radiation dose and must not be converted into dose.",
            "This bounded 2020 archive sample is historical, not real-time lunar space weather.",
        ),
        record_format="ace_npz",
        metadata_fields=(
            "cdf_version",
            "dataset_id",
            "fill_value_policy",
            "logical_source",
            "measurement_variable_count",
            "measurement_variable_names",
            "prior_validation_status",
            "prior_validation_warnings_preserved",
            "source_format",
            "source_organization",
            "source_urls",
            "time_coverage",
            "uncertainty_variable_names",
            "variables",
        ),
    ),
    "stereo_impact": DatasetSpec(
        dataset_name="STEREO IMPACT energetic-particle observations (HET/LET/SIT)",
        processed_directory="space_weather/stereo_impact",
        data_file="stereo_impact_het_201203_daily.csv.gz",
        metadata_file="stereo_impact_processing_metadata.json",
        summary_file="stereo_impact_summary_statistics.json",
        data_type="spacecraft_observation",
        scientific_limitations=(
            "These particle measurements are from STEREO-A, not the lunar surface.",
            "STEREO-A particle measurements are not astronaut radiation dose and must not be converted into dose.",
            "This 2012 archive sample is historical, not current space weather.",
        ),
        record_format="gzip_csv",
        metadata_fields=(
            "channel_count",
            "channels",
            "dataset_id",
            "electron_channel_count",
            "instrument",
            "missing_value_policy",
            "official_documentation_caveats",
            "product",
            "proton_channel_count",
            "record_layout",
        ),
    ),
    "jpl_horizons": DatasetSpec(
        dataset_name="JPL Horizons Earth-Moon and lunar ephemerides",
        processed_directory="communication_navigation/jpl_horizons",
        data_file="jpl_horizons_moon_earth_geocenter_20261114_20261121.csv",
        metadata_file="jpl_horizons_processing_metadata.json",
        summary_file="jpl_horizons_summary_statistics.json",
        data_type="computed_ephemeris",
        scientific_limitations=(
            "Horizons values are computed ephemerides; future epochs are calculations, not observations.",
            "One-way light time is not total communication delay.",
            "Two-way vacuum light time is a derived calculation, not a separate direct Horizons measurement.",
        ),
        record_format="csv",
        metadata_fields=(
            "dataset_name",
            "ephemeris_source",
            "numeric_precision_policy",
            "observer",
            "request_parameters",
            "retrieved_at_utc",
            "source",
            "source_urls",
            "source_validation_status",
            "source_validation_warnings_preserved",
            "target",
            "time",
            "variables",
        ),
    ),
    "omni_hourly": DatasetSpec(
        dataset_name="NASA OMNI2 hourly solar-wind and IMF observations",
        processed_directory="space_weather/omni",
        data_file="omni_hourly_20200101_20200201.csv",
        metadata_file="omni_processing_metadata.json",
        summary_file="omni_summary_statistics.json",
        data_type="near_earth_spacecraft_observation",
        scientific_limitations=(
            "OMNI is a merged, time-shifted near-Earth/L1 product, not a lunar-surface measurement.",
            "Solar-wind and IMF values are not astronaut radiation dose and are never converted into dose.",
            "This January 2020 interval is historical archive data, not current space weather.",
        ),
        record_format="csv",
        metadata_fields=(
            "dataset_id",
            "product",
            "source_url",
            "documentation_url",
            "source_format",
            "selection",
            "variables",
            "processed_output",
            "source_sha256",
            "processed_csv_sha256",
        ),
    ),
    "lend": DatasetSpec(
        dataset_name="LRO LEND RDR DLD/DLX one-day derived neutron observations",
        processed_directory="lunar_environment/lend",
        data_file="lend_20200101_processed.csv",
        metadata_file="lend_processing_metadata.json",
        summary_file="lend_summary_statistics.json",
        data_type="orbital_lunar_neutron_observation",
        scientific_limitations=(
            "LEND is an orbital lunar neutron detector, not a lunar-surface detector.",
            "Neutron counts and count uncertainties are not astronaut radiation dose.",
            "Neutron observations alone do not confirm water ice at a specific location.",
            "This one-day January 2020 sample is historical, not current lunar telemetry.",
        ),
        record_format="csv",
        metadata_fields=(
            "dataset_id",
            "product_identifiers",
            "source_urls",
            "source_format",
            "record_count",
            "record_join",
            "variables",
            "missing_value_policy",
            "transformations",
            "source_sha256",
            "processed_csv_sha256",
            "processed_output_readback_verified",
        ),
    ),
    "lro_spice": DatasetSpec(
        dataset_name="NASA LRO SPICE reconstructed spacecraft positions",
        processed_directory="communication_navigation/lro_spice",
        data_file="lro_spice_positions_20170915.csv",
        metadata_file="lro_spice_processing_metadata.json",
        summary_file="lro_spice_summary_statistics.json",
        data_type="computed_spice_geometry",
        scientific_limitations=(
            "Positions are computed from NASA NAIF SPICE kernels, not direct telemetry.",
            "LRO spacecraft position is not astronaut or habitat position.",
            "This September 2017 archive sample is historical, not current navigation.",
        ),
        record_format="csv",
        metadata_fields=(
            "dataset_id",
            "product_id",
            "source_urls",
            "kernel_files",
            "selection",
            "time_coverage",
            "reference_frame",
            "observer",
            "target",
            "position_units",
            "derived_fields",
            "transformations",
            "source_sha256",
            "processed_csv_sha256",
            "record_count",
        ),
    ),
    "osd53": DatasetSpec(
        dataset_name="NASA OSD-53 astronaut gene-expression study",
        processed_directory="astronaut_health/osdr",
        data_file="osd53_sample_metadata.csv",
        metadata_file="osd53_processing_metadata.json",
        summary_file="osd53_summary_statistics.json",
        data_type="historical_human_research",
        scientific_limitations=(
            "This is historical human astronaut research, not lunar astronaut data.",
            "Gene-expression values are not a medical diagnosis or health prediction.",
            "Original raw microarray data were reported unavailable by OSDR.",
            "No gene-expression value is used to create gameplay health consequences.",
        ),
        record_format="csv",
        metadata_fields=(
            "dataset_id",
            "genelab_id",
            "title",
            "organism",
            "source_urls",
            "record_count",
            "gene_summary_count",
            "variables",
            "missing_value_policy",
            "raw_data_availability",
            "privacy_policy",
            "transformations",
            "source_sha256",
            "processed_output_readback_verified",
        ),
    ),
}


def _dataset_root(spec: DatasetSpec) -> Path:
    return DATASETS_ROOT / "processed" / spec.processed_directory


def _load_catalog() -> Dict[str, Dict[str, str]]:
    try:
        with CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = csv.DictReader(stream)
            catalog = {row["dataset_name"]: row for row in rows}
    except (OSError, csv.Error, KeyError) as exc:
        raise DatasetUnavailableError(
            "The NASA dataset catalog is unavailable or malformed."
        ) from exc
    return catalog


def _catalog_row(dataset_id: str) -> tuple[DatasetSpec, Dict[str, str]]:
    spec = DATASET_SPECS.get(dataset_id)
    if spec is None:
        raise DatasetNotFoundError(f"Unknown NASA dataset ID: {dataset_id}.")
    row = _load_catalog().get(spec.dataset_name)
    if row is None:
        raise DatasetUnavailableError(
            f"Catalog metadata for dataset '{dataset_id}' is unavailable."
        )
    return spec, row


def _read_json(path: Path, dataset_id: str, label: str) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except FileNotFoundError as exc:
        raise DatasetUnavailableError(
            f"{label} is not available for dataset '{dataset_id}'."
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetUnavailableError(
            f"{label} could not be read for dataset '{dataset_id}'."
        ) from exc
    if not isinstance(value, dict):
        raise DatasetUnavailableError(
            f"{label} has an unexpected format for dataset '{dataset_id}'."
        )
    return value


def _available_files(spec: DatasetSpec) -> Dict[str, bool]:
    root = _dataset_root(spec)
    files = {
        "processed_data": (root / spec.data_file).is_file(),
        "processing_metadata": (root / spec.metadata_file).is_file(),
        "summary": (root / spec.summary_file).is_file(),
    }
    if spec.preview_file is not None:
        files["preview_data"] = (root / spec.preview_file).is_file()
    if spec.preview_metadata_file is not None:
        files["preview_metadata"] = (
            root / spec.preview_metadata_file
        ).is_file()
    return files


def _availability_status(files: Dict[str, bool]) -> str:
    if files["processed_data"]:
        return "available"
    if files.get("preview_data", False):
        return "preview_available"
    return "unavailable"


def _record_access(
    spec: DatasetSpec, files: Dict[str, bool]
) -> Dict[str, Any]:
    if spec.record_format is None:
        return {
            "available": False,
            "reason": "Record access is disabled for this large dataset.",
        }
    if spec.preview_file is not None and not files.get("preview_data", False):
        return {
            "available": False,
            "reason": "The sampled record preview is not present on this server.",
        }
    access = {
        "available": True,
        "default_page_size": DEFAULT_PAGE_SIZE,
        "maximum_page_size": MAX_PAGE_SIZE,
    }
    if spec.preview_file is not None:
        access["preview_only"] = True
        access["description"] = (
            "Records are a regular spatial sample from the full-resolution source grid."
        )
    return access


def _preview_metadata(
    spec: DatasetSpec, files: Dict[str, bool], dataset_id: str
) -> Optional[Dict[str, Any]]:
    if spec.preview_metadata_file is None or not files.get("preview_metadata", False):
        return None
    return _read_json(
        _dataset_root(spec) / spec.preview_metadata_file,
        dataset_id,
        "Preview metadata",
    )


def _processed_file_paths(spec: DatasetSpec) -> list[str]:
    paths = [
        f"datasets/processed/{spec.processed_directory}/{spec.data_file}",
        f"datasets/processed/{spec.processed_directory}/{spec.metadata_file}",
        f"datasets/processed/{spec.processed_directory}/{spec.summary_file}",
    ]
    if spec.preview_file is not None:
        paths.extend(
            (
                f"datasets/processed/{spec.processed_directory}/{spec.preview_file}",
                f"datasets/processed/{spec.processed_directory}/{spec.preview_metadata_file}",
            )
        )
    return paths


def _science_record(spec: DatasetSpec, row: Dict[str, str]) -> Dict[str, Any]:
    source_urls = [
        item.strip()
        for item in row.get("official_source_url", "").split(";")
        if item.strip()
    ]
    return {
        "dataset_name": row.get("dataset_name", spec.dataset_name),
        "category": row.get("category"),
        "scientific_purpose": row.get("scientific_purpose"),
        "important_variables": row.get("important_variables"),
        "source": {
            "organization": row.get("source_organization"),
            "urls": source_urls,
        },
        "coverage": row.get("time_coverage"),
        "geographic_or_spacecraft_coverage": row.get(
            "geographic_or_spacecraft_coverage"
        ),
        "units": row.get("units"),
        "validation_status": row.get("validation_status"),
        "data_type": spec.data_type,
        "scientific_limitations": list(spec.scientific_limitations),
    }


def _public_processing_metadata(
    spec: DatasetSpec, metadata: Dict[str, Any]
) -> Dict[str, Any]:
    public = {
        key: metadata[key]
        for key in spec.metadata_fields
        if key in metadata and key != "variables"
    }
    variable_metadata = metadata.get("variables")
    if isinstance(variable_metadata, dict):
        public["variables"] = {
            name: {
                key: value[key]
                for key in (
                    "name",
                    "type",
                    "units",
                    "fill_value",
                    "official_long_description",
                    "description",
                    "units",
                    "shape",
                    "cdf_numpy_dtype",
                    "cdf_fill_values",
                    "valid_min",
                    "valid_max",
                    "measurement_kind",
                    "validity_rule",
                    "is_direct_horizons_measurement",
                )
                if key in value
            }
            for name, value in variable_metadata.items()
            if isinstance(value, dict)
        }
    return public


def list_datasets() -> Dict[str, Any]:
    """List the supported static datasets and their file-level availability."""
    catalog = _load_catalog()
    datasets = []
    for dataset_id, spec in DATASET_SPECS.items():
        row = catalog.get(spec.dataset_name)
        if row is None:
            raise DatasetUnavailableError(
                f"Catalog metadata for dataset '{dataset_id}' is unavailable."
            )
        files = _available_files(spec)
        item = {
            "dataset_id": dataset_id,
            **_science_record(spec, row),
            "availability": {
                "status": _availability_status(files),
                **files,
            },
            "record_access": _record_access(spec, files),
            "processed_files": _processed_file_paths(spec),
        }
        datasets.append(item)
    return {"dataset_count": len(datasets), "datasets": datasets}


def get_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    spec, row = _catalog_row(dataset_id)
    files = _available_files(spec)
    metadata_path = _dataset_root(spec) / spec.metadata_file
    processing_metadata = None
    if files["processing_metadata"]:
        metadata = _read_json(metadata_path, dataset_id, "Processing metadata")
        processing_metadata = _public_processing_metadata(spec, metadata)

    return {
        "dataset_id": dataset_id,
        **_science_record(spec, row),
        "availability": {
            "status": _availability_status(files),
            **files,
        },
        "record_access": _record_access(spec, files),
        "processed_files": _processed_file_paths(spec),
        "processing_metadata": processing_metadata,
        "preview_metadata": _preview_metadata(spec, files, dataset_id),
    }


def get_dataset_summary(dataset_id: str) -> Dict[str, Any]:
    spec, row = _catalog_row(dataset_id)
    summary = _read_json(
        _dataset_root(spec) / spec.summary_file, dataset_id, "Summary statistics"
    )
    files = _available_files(spec)
    return {
        "dataset_id": dataset_id,
        **_science_record(spec, row),
        "availability": {
            "status": _availability_status(files),
            **files,
        },
        "summary": summary,
    }


def _read_csv_page(
    path: Path, page: int, page_size: int, compressed: bool
) -> tuple[list[Dict[str, str]], int]:
    opener = gzip.open if compressed else open
    try:
        with opener(path, "rt", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            records = []
            total = 0
            start_index = (page - 1) * page_size
            stop_index = start_index + page_size
            for index, row in enumerate(reader):
                if index >= start_index and index < stop_index:
                    records.append(dict(row))
                total += 1
            return records, total
    except FileNotFoundError as exc:
        raise DatasetUnavailableError(
            "Processed records are unavailable for this dataset."
        ) from exc
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DatasetUnavailableError(
            "Processed records could not be read for this dataset."
        ) from exc


def _ace_records(path: Path, page: int, page_size: int) -> tuple[list[Dict[str, Any]], int]:
    try:
        with np.load(path, allow_pickle=False) as archive:
            timestamps = archive["Epoch__utc"]
            epochs = archive["Epoch"]
            total = int(timestamps.shape[0])
            start_index = (page - 1) * page_size
            stop_index = min(start_index + page_size, total)
            variable_names = [
                name
                for name in archive.files
                if name not in {"Epoch", "Epoch__valid", "Epoch__utc", "processing_metadata_json"}
                and not name.startswith("valid_mask__")
            ]
            values = {name: archive[name] for name in variable_names}
            masks = {
                name: archive[f"valid_mask__{name}"]
                for name in variable_names
                if f"valid_mask__{name}" in archive.files
            }
            records = []
            for index in range(start_index, stop_index):
                measurements: Dict[str, Any] = {}
                for name, array in values.items():
                    value = float(array[index])
                    valid = bool(masks[name][index]) if name in masks else math.isfinite(value)
                    measurements[name] = {
                        "value": value if math.isfinite(value) else None,
                        "valid": valid,
                    }
                records.append(
                    {
                        "epoch_value": float(epochs[index]),
                        "timestamp_utc": str(timestamps[index]),
                        "measurements": measurements,
                    }
                )
            return records, total
    except FileNotFoundError as exc:
        raise DatasetUnavailableError(
            "Processed records are unavailable for this dataset."
        ) from exc
    except (OSError, ValueError, KeyError, EOFError, zipfile.BadZipFile) as exc:
        raise DatasetUnavailableError(
            "Processed records could not be read for this dataset."
        ) from exc


def get_dataset_records(
    dataset_id: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE
) -> Dict[str, Any]:
    if page < 1:
        raise ValueError("page must be at least 1")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}")

    spec, row = _catalog_row(dataset_id)
    files = _available_files(spec)
    if spec.record_format is None or (
        spec.preview_file is not None and not files.get("preview_data", False)
    ):
        raise DatasetRecordsNotAvailableError(
            "Record-level access is unavailable for this dataset; use its metadata and summary."
        )

    file_name = spec.preview_file if spec.preview_file is not None else spec.data_file
    path = _dataset_root(spec) / file_name
    if spec.record_format == "ace_npz":
        records, total = _ace_records(path, page, page_size)
    else:
        records, total = _read_csv_page(
            path, page, page_size, compressed=spec.record_format == "gzip_csv"
        )
    total_pages = math.ceil(total / page_size) if total else 0
    return {
        "dataset_id": dataset_id,
        **_science_record(spec, row),
        "records": records,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_records": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1 and total > 0,
        },
    }
