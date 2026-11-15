"""Process the bounded ACE EPAM all-variable CDF sample without altering it."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import zipfile
from typing import Any
import xml.etree.ElementTree as ET

import numpy as np
from cdflib import CDF, cdfepoch


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "space_weather" / "ace_epam"
OUTPUT_DIR = ROOT / "datasets" / "processed" / "space_weather" / "ace_epam"
DATA_FILE = "ac_h1s_epm_20200101000000_20200102000000_allvars.cdf"
VARIABLES_FILE = "cdaweb_ac_h1_epm_variables.xml"
REQUEST_FILE = "cdaweb_full_request_metadata.xml"
INSTRUMENT_DOC_FILE = "epam_l2desc.html"
OUTPUT_FILE = "ace_epam_20200101_processed.npz"
METADATA_FILE = "ace_epam_processing_metadata.json"
SUMMARY_FILE = "ace_epam_summary_statistics.json"
SCRIPT_VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [json_value(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def parse_official_variable_descriptions(path: Path) -> dict[str, dict[str, str]]:
    root = ET.parse(path).getroot()
    descriptions: dict[str, dict[str, str]] = {}
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "VariableDescription":
            continue
        fields = {
            child.tag.rsplit("}", 1)[-1]: (child.text or "").strip()
            for child in element
        }
        name = fields.get("Name", "")
        if not name or name in descriptions:
            raise ValueError(f"Missing or duplicate official CDF variable description: {name!r}")
        descriptions[name] = {
            "short_description": fields.get("ShortDescription", ""),
            "long_description": fields.get("LongDescription", ""),
        }
    if not descriptions:
        raise ValueError("No variable definitions found in the official CDAWeb XML.")
    return descriptions


def format_utc_times(epoch_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    decoded = np.asarray(cdfepoch.to_datetime(epoch_values)).astype("datetime64[ns]")
    strings = np.asarray(
        [
            np.datetime_as_string(timestamp, unit="ms") + "Z"
            for timestamp in decoded
        ],
        dtype="U24",
    )
    return decoded, strings


def _write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _cdf_attribute_text(value: Any) -> str | None:
    value = json_value(value)
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def process() -> dict[str, Any]:
    data_path = RAW_DIR / DATA_FILE
    variables_path = RAW_DIR / VARIABLES_FILE
    request_path = RAW_DIR / REQUEST_FILE
    instrument_doc_path = RAW_DIR / INSTRUMENT_DOC_FILE
    required_paths = (data_path, variables_path, request_path, instrument_doc_path)
    missing = [path.name for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required ACE EPAM source/metadata files are missing: {missing}")

    raw_files_before = {
        path.name: sha256_file(path)
        for path in sorted(RAW_DIR.iterdir())
        if path.is_file() and path.name != ".gitkeep"
    }
    official_descriptions = parse_official_variable_descriptions(variables_path)
    validation_report_path = ROOT / "datasets" / "validation_reports" / "ace_epam_validation.json"
    if not validation_report_path.is_file():
        raise FileNotFoundError(f"Existing ACE validation report is missing: {validation_report_path}")
    validation_report = json.loads(validation_report_path.read_text(encoding="utf-8"))
    if validation_report.get("status") != "PASSED_WITH_WARNINGS":
        raise ValueError(
            "Expected prior ACE validation status PASSED_WITH_WARNINGS; "
            f"found {validation_report.get('status')!r}."
        )

    cdf = CDF(data_path)
    try:
        info = cdf.cdf_info()
        global_attributes = cdf.globalattsget()
        variable_names = list(info.zVariables)
        if not variable_names or variable_names[0] != "Epoch":
            raise ValueError("Expected CDF_EPOCH support variable named Epoch.")
        data_variable_names = variable_names[1:]
        if len(data_variable_names) != 88:
            raise ValueError(f"Expected 88 measurement/uncertainty variables; found {len(data_variable_names)}.")
        if set(data_variable_names) != set(official_descriptions):
            raise ValueError("CDF variable names do not exactly match the official CDAWeb XML list.")

        epoch_values = np.asarray(cdf.varget("Epoch"))
        epoch_attributes = cdf.varattsget("Epoch")
        epoch_fills = np.asarray(epoch_attributes.get("FILLVAL", [])).reshape(-1)
        epoch_valid = np.isfinite(epoch_values)
        if epoch_fills.size:
            epoch_valid &= ~np.isin(epoch_values, epoch_fills)
        if not epoch_valid.all():
            raise ValueError("Epoch contains CDF fill or non-finite timestamps.")
        decoded_epoch, epoch_utc = format_utc_times(epoch_values)
        if decoded_epoch.size != 277:
            raise ValueError(f"Expected 277 CDF Epoch records; found {decoded_epoch.size}.")
        if not np.all(np.diff(decoded_epoch) > np.timedelta64(0, "ns")):
            raise ValueError("CDF Epoch timestamps are not strictly increasing.")

        interval_ms, interval_counts = np.unique(
            np.diff(decoded_epoch).astype("timedelta64[ms]").astype(np.int64),
            return_counts=True,
        )
        interval_distribution = {
            str(int(milliseconds // 1000)): int(count)
            for milliseconds, count in zip(interval_ms, interval_counts)
        }

        arrays: dict[str, np.ndarray] = {
            "Epoch": epoch_values.copy(),
            "Epoch__valid": epoch_valid.astype(np.bool_),
            "Epoch__utc": epoch_utc,
        }
        variable_metadata: dict[str, dict[str, Any]] = {}
        variable_summary: dict[str, dict[str, Any]] = {}
        all_fill_variables: list[str] = []
        outside_valid_range: dict[str, dict[str, int]] = {}
        uncertainty_names: list[str] = []
        measurement_names: list[str] = []
        channel_coverage: dict[str, dict[str, Any]] = {}

        for name in data_variable_names:
            values = np.asarray(cdf.varget(name))
            if values.ndim == 0 or values.shape[0] != epoch_values.size:
                raise ValueError(
                    f"{name} shape {values.shape} does not align its first dimension "
                    f"with {epoch_values.size} Epoch records."
                )
            if not np.issubdtype(values.dtype, np.number):
                raise ValueError(f"Unsupported non-numeric CDF variable {name}: {values.dtype}.")

            attributes = cdf.varattsget(name)
            fill_values = np.asarray(attributes.get("FILLVAL", [])).reshape(-1)
            if fill_values.size == 0:
                raise ValueError(f"CDF variable {name} has no FILLVAL attribute.")
            if "UNITS" not in attributes:
                raise ValueError(f"CDF variable {name} has no UNITS attribute.")

            finite_mask = np.isfinite(values)
            fill_mask = np.isin(values, fill_values)
            valid_mask = finite_mask & ~fill_mask
            valid_values = values[valid_mask]
            valid_records = np.any(valid_mask.reshape(values.shape[0], -1), axis=1)
            fill_count = int(np.count_nonzero(fill_mask))
            nonfinite_count = int(np.count_nonzero(~finite_mask))
            valid_count = int(np.count_nonzero(valid_mask))
            missing_count = int(values.size - valid_count)

            valid_min_raw = np.asarray(attributes.get("VALIDMIN", [])).reshape(-1)
            valid_max_raw = np.asarray(attributes.get("VALIDMAX", [])).reshape(-1)
            below_minimum = 0
            above_maximum = 0
            if valid_values.size and valid_min_raw.size:
                below_minimum = int(np.count_nonzero(valid_values < valid_min_raw[0]))
            if valid_values.size and valid_max_raw.size:
                above_maximum = int(np.count_nonzero(valid_values > valid_max_raw[0]))
            if below_minimum or above_maximum:
                outside_valid_range[name] = {
                    "below_validmin": below_minimum,
                    "above_validmax": above_maximum,
                }

            description = official_descriptions[name]
            short_description = description["short_description"]
            is_uncertainty = "uncertainty" in short_description.lower()
            (uncertainty_names if is_uncertainty else measurement_names).append(name)
            if valid_count == 0:
                all_fill_variables.append(name)

            arrays[name] = values.copy()
            arrays[f"valid_mask__{name}"] = valid_mask.astype(np.bool_)
            variable_info = cdf.varinq(name)
            metadata = {
                "name": name,
                "official_short_description": short_description,
                "official_long_description": description["long_description"],
                "cdf_catdesc": _cdf_attribute_text(attributes.get("CATDESC")),
                "units": _cdf_attribute_text(attributes.get("UNITS")),
                "shape": list(values.shape),
                "record_count": int(values.shape[0]),
                "numeric_value_count": int(values.size),
                "cdf_numpy_dtype": str(values.dtype),
                "cdf_variable_data_type": variable_info.Data_Type_Description,
                "cdf_num_dimensions": int(variable_info.Num_Dims),
                "cdf_dimension_sizes": [int(item) for item in variable_info.Dim_Sizes],
                "cdf_fill_values": json_value(attributes.get("FILLVAL")),
                "valid_min": json_value(attributes.get("VALIDMIN")),
                "valid_max": json_value(attributes.get("VALIDMAX")),
                "dependency_epoch": _cdf_attribute_text(attributes.get("DEPEND_0")),
                "variable_attributes": {
                    key: json_value(value)
                    for key, value in attributes.items()
                },
                "array_member": name,
                "validity_mask_array_member": f"valid_mask__{name}",
                "measurement_kind": "uncertainty" if is_uncertainty else "measurement",
                "validity_rule": "finite and not equal to any CDF FILLVAL value",
                "value_preservation": "raw CDF numeric values are stored unchanged; masks are separate",
            }
            variable_metadata[name] = metadata

            summary: dict[str, Any] = {
                "shape": list(values.shape),
                "record_count": int(values.shape[0]),
                "numeric_value_count": int(values.size),
                "valid_record_count": int(np.count_nonzero(valid_records)),
                "records_with_no_valid_values": int(values.shape[0] - np.count_nonzero(valid_records)),
                "valid_value_count": valid_count,
                "fill_value_count": fill_count,
                "nonfinite_value_count": nonfinite_count,
                "missing_or_invalid_value_count": missing_count,
                "fill_values": json_value(attributes.get("FILLVAL")),
                "units": _cdf_attribute_text(attributes.get("UNITS")),
                "measurement_kind": metadata["measurement_kind"],
                "description": description["long_description"],
                "valid_min": json_value(attributes.get("VALIDMIN")),
                "valid_max": json_value(attributes.get("VALIDMAX")),
                "values_below_valid_min": below_minimum,
                "values_above_valid_max": above_maximum,
                "minimum": float(np.min(valid_values)) if valid_count else None,
                "maximum": float(np.max(valid_values)) if valid_count else None,
                "mean": float(np.mean(valid_values, dtype=np.float64)) if valid_count else None,
                "median": float(np.median(valid_values)) if valid_count else None,
            }
            variable_summary[name] = summary
            if not is_uncertainty:
                channel_coverage[name] = {
                    "description": description["long_description"],
                    "units": summary["units"],
                    "valid_records": summary["valid_record_count"],
                    "total_records": int(values.shape[0]),
                    "coverage_fraction": (
                        float(summary["valid_record_count"] / values.shape[0])
                        if values.shape[0]
                        else None
                    ),
                    "all_values_are_fill_or_nonfinite": valid_count == 0,
                }

        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        npz_path = output_dir / OUTPUT_FILE
        npz_temporary = output_dir / (OUTPUT_FILE + ".tmp")
        arrays["processing_metadata_json"] = np.asarray(
            json.dumps(
                {
                    "dataset_id": "AC_H1_EPM",
                    "logical_source": _cdf_attribute_text(global_attributes.get("Logical_source")),
                    "time_variable": "Epoch",
                    "time_utc_member": "Epoch__utc",
                    "time_representation": "CDF_EPOCH raw values plus ISO-8601 UTC strings",
                    "variable_metadata": variable_metadata,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        _write_deterministic_npz(npz_temporary, arrays)

        with np.load(npz_temporary, allow_pickle=False) as archive:
            if set(archive.files) != set(arrays):
                raise ValueError("Processed NPZ members differ from generated time series and masks.")
            if not np.array_equal(archive["Epoch"], epoch_values):
                raise ValueError("Reopened CDF Epoch values differ from the source.")
            if not np.array_equal(archive["Epoch__utc"], epoch_utc):
                raise ValueError("Reopened UTC timestamp strings differ from decoded CDF Epoch.")
            for name in data_variable_names:
                if not np.array_equal(archive[name], arrays[name], equal_nan=True):
                    raise ValueError(f"Reopened processed values differ from the source for {name}.")
                if not np.array_equal(
                    archive[f"valid_mask__{name}"],
                    np.isfinite(arrays[name])
                    & ~np.isin(arrays[name], np.asarray(variable_metadata[name]["cdf_fill_values"])),
                ):
                    raise ValueError(f"Reopened validity mask is inconsistent for {name}.")
        os.replace(npz_temporary, npz_path)

        global_metadata = {
            key: json_value(global_attributes[key])
            for key in (
                "TITLE",
                "Project",
                "Data_type",
                "Generation_date",
                "Logical_source",
                "Logical_source_description",
                "Time_resolution",
                "CDAWEB_PARENTS",
                "DOI",
                "spase_DatasetResourceID",
            )
            if key in global_attributes
        }
        cdf_version = str(info.Version)
    finally:
        del cdf

    raw_files_after = {
        path.name: sha256_file(path)
        for path in sorted(RAW_DIR.iterdir())
        if path.is_file() and path.name != ".gitkeep"
    }
    if raw_files_before != raw_files_after:
        raise RuntimeError("One or more original ACE EPAM raw files changed during processing.")

    if len(measurement_names) != 44 or len(uncertainty_names) != 44:
        raise ValueError(
            "Official metadata did not yield 44 measurement and 44 uncertainty "
            f"variables: {len(measurement_names)}, {len(uncertainty_names)}."
        )

    preserved_warnings = list(validation_report.get("warnings", []))
    start_utc = str(epoch_utc[0])
    end_utc = str(epoch_utc[-1])
    metadata = {
        "dataset_name": "ACE EPAM AC_H1_EPM five-minute Level 2 sample",
        "dataset_id": "AC_H1_EPM",
        "logical_source": _cdf_attribute_text(global_attributes.get("Logical_source")),
        "source_cdf_file": DATA_FILE,
        "source_sha256": raw_files_before[DATA_FILE],
        "source_files_sha256": raw_files_before,
        "source_file_size_bytes": data_path.stat().st_size,
        "source_format": "NASA Common Data Format (CDF)",
        "cdf_version": cdf_version,
        "source_organization": "NASA SPDF / CDAWeb; ACE Science Center EPAM team",
        "source_urls": {
            "spdf_epam_archive": "https://spdf.gsfc.nasa.gov/pub/data/ace/epam/",
            "cdaweb_dataset": "https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/AC_H1_EPM/",
            "instrument_documentation": "https://izw1.caltech.edu/ACE/ASC/level2/epam_l2desc.html",
        },
        "global_cdf_metadata": global_metadata,
        "time": {
            "cdf_variable": "Epoch",
            "cdf_data_type": "CDF_EPOCH",
            "source_dtype": str(epoch_values.dtype),
            "cdf_units_attribute": _cdf_attribute_text(epoch_attributes.get("UNITS")),
            "record_count": int(epoch_values.size),
            "utc_start": start_utc,
            "utc_end": end_utc,
            "format": "ISO-8601 UTC strings with millisecond precision, ending in Z; original CDF_EPOCH values also preserved",
            "interval_distribution_seconds_to_interval_count": interval_distribution,
            "strictly_increasing": True,
        },
        "measurement_variable_count": len(measurement_names),
        "uncertainty_variable_count": len(uncertainty_names),
        "total_data_variable_count": len(data_variable_names),
        "measurement_variable_names": measurement_names,
        "uncertainty_variable_names": uncertainty_names,
        "variables": variable_metadata,
        "fill_value_policy": (
            "CDF FILLVAL and non-finite numeric values are identified by separate boolean masks. "
            "All original CDF value arrays are retained unchanged, including fill values and "
            "variables containing no valid values. No interpolation or substitution is performed."
        ),
        "processing_script": "datasets/scripts/process_ace_epam.py",
        "processing_script_version": SCRIPT_VERSION,
        "processed_file": OUTPUT_FILE,
        "processed_format": "Deterministic compressed NumPy .npz; use numpy.load(..., allow_pickle=False)",
        "processed_size_bytes": npz_path.stat().st_size,
        "processed_sha256": sha256_file(npz_path),
        "archive_reopened_and_arrays_verified": True,
        "raw_files_sha256_unchanged": True,
        "prior_validation_status": validation_report["status"],
        "prior_validation_warnings_preserved": preserved_warnings,
    }
    summary = {
        "dataset_name": metadata["dataset_name"],
        "source_file": DATA_FILE,
        "processed_file": OUTPUT_FILE,
        "record_count": int(epoch_values.size),
        "time_coverage_utc": {"start": start_utc, "end": end_utc},
        "time_interval_distribution_seconds_to_interval_count": interval_distribution,
        "total_data_variable_count": len(data_variable_names),
        "measurement_variable_count": len(measurement_names),
        "uncertainty_variable_count": len(uncertainty_names),
        "total_numeric_measurement_and_uncertainty_values": int(
            sum(item["numeric_value_count"] for item in variable_summary.values())
        ),
        "total_valid_numeric_values": int(
            sum(item["valid_value_count"] for item in variable_summary.values())
        ),
        "total_cdf_fill_values": int(
            sum(item["fill_value_count"] for item in variable_summary.values())
        ),
        "total_nonfinite_values": int(
            sum(item["nonfinite_value_count"] for item in variable_summary.values())
        ),
        "measurement_variables": measurement_names,
        "uncertainty_variables": uncertainty_names,
        "variables": variable_summary,
        "all_fill_or_nonfinite_variable_count": len(all_fill_variables),
        "all_fill_or_nonfinite_variables": all_fill_variables,
        "available_channel_coverage": channel_coverage,
        "variables_outside_cdf_validmin_validmax": outside_valid_range,
        "original_validation_warnings_preserved": preserved_warnings,
        "scientific_limitation": (
            "ACE EPAM measurements are collected at the ACE spacecraft near Sun-Earth L1, "
            "not at the Moon. They do not measure lunar surface exposure or astronaut dose "
            "and must not be used as a real-time lunar condition or dose proxy."
        ),
    }
    _write_json(OUTPUT_DIR / METADATA_FILE, metadata)
    _write_json(OUTPUT_DIR / SUMMARY_FILE, summary)
    return {"metadata": metadata, "summary": summary}


if __name__ == "__main__":
    result = process()
    summary = result["summary"]
    print(
        f"ACE EPAM processing complete: {summary['record_count']} records, "
        f"{summary['total_data_variable_count']} variables, "
        f"{summary['all_fill_or_nonfinite_variable_count']} all-fill variables."
    )
    for filename in (OUTPUT_FILE, METADATA_FILE, SUMMARY_FILE):
        path = OUTPUT_DIR / filename
        print(f"{path}: {path.stat().st_size} bytes")
    for warning in result["metadata"]["prior_validation_warnings_preserved"]:
        print(f"WARNING: {warning}")
