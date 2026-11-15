"""Validate the bounded ACE EPAM Level 2 CDF sample and its source metadata."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from cdflib import CDF, cdfepoch


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "space_weather" / "ace_epam"
REPORT_PATH = ROOT / "datasets" / "validation_reports" / "ace_epam_validation.json"

DATA_FILE = "ac_h1s_epm_20200101000000_20200102000000_allvars.cdf"
REQUEST_FILE = "cdaweb_full_request_metadata.xml"
VARIABLES_FILE = "cdaweb_ac_h1_epm_variables.xml"
INSTRUMENT_DOC_FILE = "epam_l2desc.html"
REQUEST_START = "2020-01-01T00:00:00.000Z"
REQUEST_END = "2020-01-02T00:00:00.000Z"
EXPECTED_LOGICAL_SOURCE = "AC_H1S_EPM"
EXPECTED_DATA_TYPE = "H1>5-minute Level 2 data"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def xml_text(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local_name:
            return (element.text or "").strip()
    return None


def attribute_value(value: Any) -> Any:
    array = np.asarray(value)
    if array.size == 1:
        value = array.reshape(-1)[0]
        if isinstance(value, np.generic):
            value = value.item()
        return value
    return [
        item.item() if isinstance(item, np.generic) else item
        for item in array.reshape(-1).tolist()
    ]


def iso_utc(value: np.datetime64) -> str:
    return np.datetime_as_string(value, unit="ms") + "Z"


def validate() -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat()
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}
    files: dict[str, Any] = {}
    result: dict[str, Any] = {
        "checked_at_utc": checked_at,
        "dataset_name": "ACE EPAM AC_H1_EPM 5-minute Level 2 subset",
        "dataset_id": "AC_H1_EPM",
        "logical_source": EXPECTED_LOGICAL_SOURCE,
        "official_source_url": (
            "https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/"
            "datasets/AC_H1_EPM/"
        ),
        "requested_interval_utc": {
            "start": REQUEST_START,
            "end": REQUEST_END,
        },
        "raw_directory": str(RAW_DIR),
        "files": files,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }

    required = (DATA_FILE, REQUEST_FILE, VARIABLES_FILE, INSTRUMENT_DOC_FILE)
    for name in required:
        path = RAW_DIR / name
        exists = path.is_file()
        checks[f"{name}_exists"] = exists
        if not exists:
            errors.append(f"Required source or documentation file is missing: {name}")
            continue
        files[name] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    if errors:
        result["status"] = "FAILED"
        _write_report(result)
        return result

    request_path = RAW_DIR / REQUEST_FILE
    try:
        request_root = ET.parse(request_path).getroot()
        declared_size = int(xml_text(request_root, "Length") or "-1")
        request_start = xml_text(request_root, "StartTime")
        request_end = xml_text(request_root, "EndTime")
        mime_type = xml_text(request_root, "MimeType")
        checks["request_metadata_file_size_matches"] = (
            declared_size == files[DATA_FILE]["size_bytes"]
        )
        checks["request_metadata_format_is_cdf"] = mime_type == "application/x-cdf"
        checks["request_metadata_interval_matches"] = (
            request_start == REQUEST_START and request_end == REQUEST_END
        )
        if not checks["request_metadata_file_size_matches"]:
            errors.append(
                "The downloaded CDF byte size does not match the size reported "
                "by CDAWeb."
            )
        if not checks["request_metadata_format_is_cdf"]:
            errors.append(f"CDAWeb reported an unexpected MIME type: {mime_type!r}.")
        if not checks["request_metadata_interval_matches"]:
            errors.append(
                "The CDAWeb response interval does not match the requested interval."
            )
        metadata_warnings = [
            (element.text or "").strip()
            for element in request_root.iter()
            if element.tag.rsplit("}", 1)[-1] == "Warning"
        ]
    except (ET.ParseError, OSError, ValueError) as exc:
        errors.append(f"Could not validate the CDAWeb request metadata: {exc}")
        metadata_warnings = []

    try:
        variables_root = ET.parse(RAW_DIR / VARIABLES_FILE).getroot()
        documented_variables = [
            (element.text or "").strip()
            for element in variables_root.iter()
            if element.tag.rsplit("}", 1)[-1] == "Name"
        ]
        checks["official_variable_metadata_is_nonempty"] = bool(documented_variables)
    except (ET.ParseError, OSError) as exc:
        errors.append(f"Could not read the official variable metadata XML: {exc}")
        documented_variables = []

    cdf_details: dict[str, Any] = {}
    try:
        cdf = CDF(RAW_DIR / DATA_FILE)
        info = cdf.cdf_info()
        global_attributes = cdf.globalattsget()
        z_variables = list(info.zVariables)
        data_variables = [name for name in z_variables if name != "Epoch"]
        checks["cdf_has_expected_epoch_variable"] = "Epoch" in z_variables
        checks["cdf_has_documented_measurement_variables"] = bool(data_variables)
        checks["cdf_variables_match_official_list"] = (
            set(data_variables) == set(documented_variables)
            and len(data_variables) == len(documented_variables)
        )
        checks["cdf_logical_source_matches"] = (
            attribute_value(global_attributes.get("Logical_source"))
            == EXPECTED_LOGICAL_SOURCE
        )
        checks["cdf_data_type_matches"] = (
            attribute_value(global_attributes.get("Data_type"))
            == EXPECTED_DATA_TYPE
        )
        if not checks["cdf_variables_match_official_list"]:
            errors.append(
                "CDF variables do not match the names in the official CDAWeb "
                "variable metadata."
            )
        if not checks["cdf_logical_source_matches"]:
            errors.append("The CDF Logical_source is not AC_H1S_EPM.")
        if not checks["cdf_data_type_matches"]:
            errors.append("The CDF does not identify itself as 5-minute Level 2 data.")

        epoch = np.asarray(cdf.varget("Epoch"))
        epoch_attributes = cdf.varattsget("Epoch")
        epoch_fill = np.asarray(epoch_attributes.get("FILLVAL", [])).reshape(-1)
        epoch_valid = np.isfinite(epoch)
        if epoch_fill.size:
            epoch_valid &= ~np.isin(epoch, epoch_fill)
        checks["epoch_has_no_fill_or_nonfinite_records"] = bool(epoch_valid.all())
        if not epoch_valid.all():
            errors.append("Epoch contains a fill or non-finite value.")

        decoded = np.asarray(cdfepoch.to_datetime(epoch[epoch_valid])).astype(
            "datetime64[ns]"
        )
        monotonic = decoded.size > 0 and bool(
            np.all(np.diff(decoded) > np.timedelta64(0, "ns"))
        )
        checks["epoch_is_strictly_increasing"] = monotonic
        if not monotonic:
            errors.append("Epoch is empty or not strictly increasing.")

        expected_start = np.datetime64(REQUEST_START.replace("Z", ""), "ns")
        expected_end = np.datetime64(REQUEST_END.replace("Z", ""), "ns")
        within_request = bool(
            decoded.size
            and decoded[0] >= expected_start
            and decoded[-1] <= expected_end
        )
        checks["epoch_is_within_requested_interval"] = within_request
        if not within_request:
            errors.append("Decoded Epoch coverage falls outside the requested interval.")

        cadence_seconds: dict[str, int] = {}
        if decoded.size > 1:
            differences = np.diff(decoded).astype("timedelta64[ms]").astype(np.int64)
            unique, counts = np.unique(differences, return_counts=True)
            cadence_seconds = {
                str(int(milliseconds // 1000)): int(count)
                for milliseconds, count in zip(unique, counts)
            }
            if any(milliseconds != 300_000 for milliseconds in unique):
                warnings.append(
                    "Epoch intervals are not uniformly 5 minutes: "
                    f"{cadence_seconds} (seconds: interval count). Original timestamps "
                    "are retained unchanged."
                )

        if len(metadata_warnings):
            warnings.append(
                "CDAWeb response metadata contains "
                f"{len(metadata_warnings)} dimension-reformation warnings. The CDF "
                "was readable and every data variable was checked for record alignment."
            )

        variable_summaries: dict[str, Any] = {}
        all_missing_variables: list[str] = []
        out_of_bounds_variables: dict[str, int] = {}
        for name in data_variables:
            values = np.asarray(cdf.varget(name))
            attributes = cdf.varattsget(name)
            aligned = values.ndim >= 1 and values.shape[0] == epoch.size
            checks[f"{name}_record_count_matches_epoch"] = aligned
            if not aligned:
                errors.append(
                    f"{name} has shape {values.shape}; its first dimension must "
                    f"match the {epoch.size} Epoch records."
                )

            fill_values = np.asarray(attributes.get("FILLVAL", [])).reshape(-1)
            finite_mask = (
                np.isfinite(values)
                if np.issubdtype(values.dtype, np.number)
                else np.ones(values.shape, dtype=bool)
            )
            fill_mask = (
                np.isin(values, fill_values)
                if fill_values.size
                else np.zeros(values.shape, dtype=bool)
            )
            present_mask = finite_mask & ~fill_mask
            present_count = int(present_mask.sum())
            missing_count = int(values.size - present_count)
            if not fill_values.size:
                errors.append(f"{name} is missing the CDF FILLVAL attribute.")
            if not attribute_value(attributes.get("UNITS")):
                errors.append(f"{name} is missing the CDF UNITS attribute.")

            valid_min = np.asarray(attributes.get("VALIDMIN", [])).reshape(-1)
            valid_max = np.asarray(attributes.get("VALIDMAX", [])).reshape(-1)
            below_min = 0
            above_max = 0
            if present_count and np.issubdtype(values.dtype, np.number):
                if valid_min.size:
                    below_min = int(np.count_nonzero(values[present_mask] < valid_min[0]))
                if valid_max.size:
                    above_max = int(np.count_nonzero(values[present_mask] > valid_max[0]))
            outside_count = below_min + above_max
            if outside_count:
                out_of_bounds_variables[name] = outside_count
            if present_count == 0:
                all_missing_variables.append(name)

            variable_summaries[name] = {
                "shape": list(values.shape),
                "records_with_values": present_count,
                "missing_or_nonfinite_values": missing_count,
                "fill_values": attribute_value(attributes.get("FILLVAL")),
                "units": attribute_value(attributes.get("UNITS")),
                "valid_min": attribute_value(attributes.get("VALIDMIN")),
                "valid_max": attribute_value(attributes.get("VALIDMAX")),
                "values_below_valid_min": below_min,
                "values_above_valid_max": above_max,
                "description": attribute_value(attributes.get("CATDESC")),
            }

        if all_missing_variables:
            warnings.append(
                "These variables contain only documented CDF fill/non-finite values "
                f"in this interval: {', '.join(all_missing_variables)}."
            )
        if out_of_bounds_variables:
            warnings.append(
                "These variables contain values outside their CDF VALIDMIN/VALIDMAX "
                f"metadata: {out_of_bounds_variables}. Values were not changed; "
                "consult the EPAM product documentation before treating these "
                "attributes as physical rejection criteria."
            )

        cdf_details = {
            "format": "NASA Common Data Format",
            "cdf_version": str(info.Version),
            "logical_source": attribute_value(global_attributes.get("Logical_source")),
            "data_type": attribute_value(global_attributes.get("Data_type")),
            "time_resolution": attribute_value(
                global_attributes.get("Time_resolution")
            ),
            "generation_date": attribute_value(
                global_attributes.get("Generation_date")
            ),
            "source_parent_files": attribute_value(
                global_attributes.get("CDAWEB_PARENTS")
            ),
            "record_count": int(epoch.size),
            "time_coverage_utc": (
                {"start": iso_utc(decoded[0]), "end": iso_utc(decoded[-1])}
                if decoded.size
                else None
            ),
            "cadence_seconds_and_interval_counts": cadence_seconds,
            "measurement_and_uncertainty_variable_count": len(data_variables),
            "all_missing_variables": all_missing_variables,
            "out_of_cdf_bounds_variables": out_of_bounds_variables,
            "variables": variable_summaries,
        }
    except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError) as exc:
        errors.append(f"Could not read or validate the NASA CDF: {exc}")

    result["cdf"] = cdf_details
    result["cdaweb_response_warning_count"] = len(metadata_warnings)
    result["status"] = "FAILED" if errors else (
        "PASSED_WITH_WARNINGS" if warnings else "PASSED"
    )
    _write_report(result)
    return result


def _write_report(result: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    report = validate()
    print(
        f"ACE EPAM validation: {report['status']}; "
        f"errors={len(report['errors'])}; warnings={len(report['warnings'])}"
    )
    print(f"Report: {REPORT_PATH}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    raise SystemExit(1 if report["errors"] else 0)
