"""Validate the downloaded PDS LOLA LDEM_16 global elevation image."""

from __future__ import annotations

import array
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "datasets" / "raw" / "lunar_environment" / "lola"
REPORT_PATH = ROOT / "datasets" / "validation_reports" / "lola_ldem_16_validation.json"
EXPECTED_ROWS = 2_880
EXPECTED_COLUMNS = 5_760
EXPECTED_PRODUCT_ID = "LDEM_16"
EXPECTED_LOGICAL_IDENTIFIER = "urn:nasa:pds:lro_lola_rdr:data_gridded:ldem_16"
EXPECTED_FILE_SIZES = {
    "ldem_16.img": 33_177_600,
    "ldem_16.lbl": 5_121,
    "ldem_16.xml": 11_941,
    "dsmap.cat": 7_378,
    "rdrsis.pdf": 802_914,
}


def parse_label(path: Path) -> dict[str, str]:
    label: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.match(r"\s*(\^?[A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$", line)
        if match:
            label[match.group(1)] = match.group(2).strip().strip('"')
    return label


def xml_values(root: ET.Element, local_name: str) -> list[str]:
    return [
        (element.text or "").strip()
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == local_name
    ]


def first_xml_value(root: ET.Element, local_name: str) -> str:
    values = xml_values(root, local_name)
    if not values:
        raise ValueError(f"Missing XML metadata element: {local_name}")
    return values[0]


def parse_number(value: str, key: str) -> float:
    match = re.search(r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?", value)
    if not match:
        raise ValueError(f"Could not parse numeric label value {key}: {value}")
    return float(match.group())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate() -> dict[str, Any]:
    names = ("ldem_16.img", "ldem_16.lbl", "ldem_16.xml", "dsmap.cat", "rdrsis.pdf")
    files = {name: RAW_DIR / name for name in names}
    checks: dict[str, bool] = {}
    errors: list[str] = []
    warnings = [
        "The PDS label defines no missing-value sentinel; no value is treated as missing based on an assumed convention.",
        "LDEM_16 is a global 1,895.21 m/pixel grid and is suitable only for broad terrain context, not fine landing hazard assessment.",
        "The raster checksum is recorded for local integrity tracking; an independent source checksum was not listed with this product.",
    ]
    result: dict[str, Any] = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": "LRO LOLA Gridded Digital Elevation Model LDEM_16",
        "data_set_id": "LRO-L-LOLA-4-GDR-V1.0",
        "product_id": EXPECTED_PRODUCT_ID,
        "logical_identifier": EXPECTED_LOGICAL_IDENTIFIER,
        "official_source_url": (
            "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/"
            "lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_16.img"
        ),
        "raw_directory": str(RAW_DIR),
        "files": {},
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }

    for name, path in files.items():
        exists = path.is_file()
        checks[f"{name}_exists"] = exists
        if not exists:
            errors.append(f"Required source or documentation file is missing: {name}")
        else:
            size_bytes = path.stat().st_size
            expected_size = EXPECTED_FILE_SIZES[name]
            checks[f"{name}_size_matches_pds_source"] = size_bytes == expected_size
            if size_bytes != expected_size:
                errors.append(
                    f"{name} has {size_bytes} bytes; the verified PDS source listing "
                    f"reported {expected_size}."
                )
            result["files"][name] = {
                "size_bytes": size_bytes,
                "sha256": sha256_file(path),
            }

    image_path = files["ldem_16.img"]
    label_path = files["ldem_16.lbl"]
    xml_path = files["ldem_16.xml"]
    map_path = files["dsmap.cat"]

    if all(path.is_file() for path in (image_path, label_path, xml_path, map_path)):
        try:
            label = parse_label(label_path)
            pds_xml = ET.parse(xml_path).getroot()
            map_text = map_path.read_text(encoding="ascii")
            pdf_header = files["rdrsis.pdf"].read_bytes()[:5]
            checks["rdrsis_is_pdf"] = pdf_header == b"%PDF-"
            if pdf_header != b"%PDF-":
                errors.append("The downloaded LOLA RDR SIS does not have a PDF signature.")

            expected_metadata = {
                "PRODUCT_ID": EXPECTED_PRODUCT_ID,
                "DATA_SET_ID": "LRO-L-LOLA-4-GDR-V1.0",
                "FILE_RECORDS": str(EXPECTED_ROWS),
                "RECORD_BYTES": str(EXPECTED_COLUMNS * 2),
                "LINES": str(EXPECTED_ROWS),
                "LINE_SAMPLES": str(EXPECTED_COLUMNS),
                "SAMPLE_TYPE": "LSB_INTEGER",
                "SAMPLE_BITS": "16",
                "UNIT": "METER",
            }
            for key, expected in expected_metadata.items():
                actual = label.get(key)
                ok = actual == expected
                checks[f"label_{key.lower()}_matches"] = ok
                if not ok:
                    errors.append(f"PDS label {key} is {actual!r}; expected {expected!r}.")

            byte_count = image_path.stat().st_size
            expected_bytes = EXPECTED_ROWS * EXPECTED_COLUMNS * 2
            checks["image_size_matches_pds_dimensions"] = byte_count == expected_bytes
            checks["image_size_matches_source_listing"] = (
                byte_count == EXPECTED_FILE_SIZES["ldem_16.img"]
            )
            if byte_count != expected_bytes:
                errors.append(
                    f"Image has {byte_count} bytes; PDS dimensions require {expected_bytes}."
                )
            if byte_count != EXPECTED_FILE_SIZES["ldem_16.img"]:
                errors.append(
                    "Image has "
                    f"{byte_count} bytes; the PDS directory listed "
                    f"{EXPECTED_FILE_SIZES['ldem_16.img']}."
                )

            image_bytes = image_path.read_bytes()
            samples = array.array("h")
            samples.frombytes(image_bytes)
            if sys.byteorder != "little":
                samples.byteswap()
            actual_min = min(samples)
            actual_max = max(samples)
            documented_min = int(parse_number(label["MINIMUM"], "MINIMUM"))
            documented_max = int(parse_number(label["MAXIMUM"], "MAXIMUM"))
            checks["sample_count_matches_pds_dimensions"] = len(samples) == EXPECTED_ROWS * EXPECTED_COLUMNS
            checks["observed_sample_range_within_documented_range"] = (
                documented_min <= actual_min <= actual_max <= documented_max
            )
            if len(samples) != EXPECTED_ROWS * EXPECTED_COLUMNS:
                errors.append("Decoded sample count does not match the PDS image dimensions.")
            if not documented_min <= actual_min <= actual_max <= documented_max:
                errors.append(
                    f"Observed raw sample range [{actual_min}, {actual_max}] is outside "
                    f"the documented range [{documented_min}, {documented_max}]."
                )
            if actual_min != documented_min or actual_max != documented_max:
                warnings.append(
                    "Observed raster extrema "
                    f"[{actual_min}, {actual_max}] differ from the PDS label's "
                    f"MINIMUM/MAXIMUM [{documented_min}, {documented_max}], but remain "
                    "within those documented bounds. Confirm this label/data extrema "
                    "difference with the archive before interpreting extreme values."
                )

            scaling_factor = parse_number(label["SCALING_FACTOR"], "SCALING_FACTOR")
            value_offset = parse_number(label["OFFSET"], "OFFSET")
            result["raster"] = {
                "rows": EXPECTED_ROWS,
                "columns": EXPECTED_COLUMNS,
                "sample_count": len(samples),
                "sample_type": "signed 16-bit little-endian integer",
                "stored_sample_minimum": actual_min,
                "stored_sample_maximum": actual_max,
                "pds_label_minimum_maximum": [documented_min, documented_max],
                "observed_range_within_pds_label_bounds": (
                    documented_min <= actual_min <= actual_max <= documented_max
                ),
                "height_unit": label["UNIT"],
                "height_scaling_factor": scaling_factor,
                "reference_radius_offset_m": value_offset,
                "scaled_height_range_m": [
                    actual_min * scaling_factor,
                    actual_max * scaling_factor,
                ],
                "documented_missing_values": (
                    re.findall(
                        r"(?im)^\s*(?:MISSING_CONSTANT|NULL|CORE_NULL)\s*=\s*(.*?)\s*$",
                        label_path.read_text(encoding="ascii"),
                    )
                ),
                "missing_value_policy": "The PDS3 product label defines no missing-value sentinel.",
            }

            logical_identifier = first_xml_value(pds_xml, "logical_identifier")
            title = first_xml_value(pds_xml, "title")
            xml_start = first_xml_value(pds_xml, "start_date_time").removesuffix("Z")
            xml_stop = first_xml_value(pds_xml, "stop_date_time").removesuffix("Z")
            checks["xml_identifier_matches_pds_label"] = (
                logical_identifier == EXPECTED_LOGICAL_IDENTIFIER
            )
            checks["xml_title_identifies_product"] = "LDEM_16" in title
            checks["xml_observation_dates_match_pds_label"] = (
                xml_start == label["START_TIME"] and xml_stop == label["STOP_TIME"]
            )
            xml_latitude_type = first_xml_value(pds_xml, "latitude_type")
            image_array = next(
                element
                for element in pds_xml.iter()
                if element.tag.rsplit("}", 1)[-1] == "Array_2D_Image"
            )
            xml_dimensions = xml_values(image_array, "elements")
            xml_sample_type = first_xml_value(image_array, "data_type")
            xml_unit = first_xml_value(image_array, "unit")
            xml_scaling = parse_number(
                first_xml_value(image_array, "scaling_factor"), "XML scaling_factor"
            )
            xml_offset = parse_number(
                first_xml_value(image_array, "value_offset"), "XML value_offset"
            )
            xml_minimum = parse_number(
                first_xml_value(image_array, "minimum"), "XML minimum"
            )
            xml_maximum = parse_number(
                first_xml_value(image_array, "maximum"), "XML maximum"
            )
            checks["xml_dimensions_match_pds3_label"] = xml_dimensions == [
                str(EXPECTED_ROWS),
                str(EXPECTED_COLUMNS),
            ]
            checks["xml_sample_type_matches_pds3_label"] = xml_sample_type == "SignedLSB2"
            checks["xml_unit_matches_pds3_label"] = xml_unit == label["UNIT"]
            checks["xml_scaling_and_offset_match_pds3_label"] = (
                xml_scaling == parse_number(label["SCALING_FACTOR"], "SCALING_FACTOR")
                and xml_offset == parse_number(label["OFFSET"], "OFFSET")
            )
            checks["xml_declared_range_matches_pds3_label"] = (
                xml_minimum == parse_number(label["MINIMUM"], "MINIMUM")
                and xml_maximum == parse_number(label["MAXIMUM"], "MAXIMUM")
            )
            if not checks["xml_dimensions_match_pds3_label"]:
                errors.append(f"PDS4 image dimensions differ from the PDS3 label: {xml_dimensions}")
            if not checks["xml_sample_type_matches_pds3_label"]:
                errors.append(f"Unexpected PDS4 image sample type: {xml_sample_type}")
            if not checks["xml_unit_matches_pds3_label"]:
                errors.append(f"PDS4 unit {xml_unit!r} differs from PDS3 unit {label['UNIT']!r}.")
            if not checks["xml_scaling_and_offset_match_pds3_label"]:
                errors.append("PDS3 and PDS4 scale/offset metadata do not agree.")
            if not checks["xml_declared_range_matches_pds3_label"]:
                errors.append("PDS3 and PDS4 declared sample extrema do not agree.")
            if logical_identifier != EXPECTED_LOGICAL_IDENTIFIER:
                errors.append(f"Unexpected PDS4 logical identifier: {logical_identifier}")
            if "LDEM_16" not in title:
                errors.append(f"Unexpected PDS4 title: {title}")
            if xml_start != label["START_TIME"] or xml_stop != label["STOP_TIME"]:
                errors.append("PDS3 and PDS4 observation periods do not agree.")

            bounds = {
                "minimum_latitude_degrees": parse_number(label["MINIMUM_LATITUDE"], "MINIMUM_LATITUDE"),
                "maximum_latitude_degrees": parse_number(label["MAXIMUM_LATITUDE"], "MAXIMUM_LATITUDE"),
                "westernmost_longitude_degrees": parse_number(label["WESTERNMOST_LONGITUDE"], "WESTERNMOST_LONGITUDE"),
                "easternmost_longitude_degrees": parse_number(label["EASTERNMOST_LONGITUDE"], "EASTERNMOST_LONGITUDE"),
            }
            resolution = parse_number(label["MAP_RESOLUTION"], "MAP_RESOLUTION")
            checks["label_geographic_bounds_are_valid"] = (
                -90 <= bounds["minimum_latitude_degrees"] < bounds["maximum_latitude_degrees"] <= 90
                and 0 <= bounds["westernmost_longitude_degrees"] < bounds["easternmost_longitude_degrees"] <= 360
            )
            checks["grid_dimensions_match_bounds_and_resolution"] = (
                (bounds["maximum_latitude_degrees"] - bounds["minimum_latitude_degrees"]) * resolution == EXPECTED_ROWS
                and (bounds["easternmost_longitude_degrees"] - bounds["westernmost_longitude_degrees"]) * resolution == EXPECTED_COLUMNS
            )
            checks["map_projection_reference_is_present"] = (
                label.get("MAP_PROJECTION_TYPE") == "SIMPLE CYLINDRICAL"
                and "^DATA_SET_MAP_PROJECTION" in label
                and "SIMPLE CYLINDRICAL" in map_text
            )
            checks["xml_latitude_reference_is_planetocentric"] = (
                xml_latitude_type.lower() == "planetocentric"
            )
            if not checks["label_geographic_bounds_are_valid"]:
                errors.append("PDS label geographic bounds are invalid.")
            if not checks["grid_dimensions_match_bounds_and_resolution"]:
                errors.append("Grid dimensions do not agree with the PDS bounds and map resolution.")
            if not checks["map_projection_reference_is_present"]:
                errors.append("PDS map projection reference is missing or inconsistent.")
            if not checks["xml_latitude_reference_is_planetocentric"]:
                errors.append(f"Unexpected PDS4 latitude type: {xml_latitude_type}")

            result["metadata"] = {
                "title": title,
                "observation_period": {"start": label["START_TIME"], "stop": label["STOP_TIME"]},
                "coverage": bounds,
                "map_projection": label["MAP_PROJECTION_TYPE"],
                "coordinate_system": label["COORDINATE_SYSTEM_NAME"],
                "latitude_type": xml_latitude_type,
                "longitude_direction": label["POSITIVE_LONGITUDE_DIRECTION"],
                "map_resolution_pixels_per_degree": resolution,
                "map_scale_m_per_pixel": parse_number(label["MAP_SCALE"], "MAP_SCALE"),
                "geographic_datum_reference": "LOLA product uses reference radius 1,737,400 m; topography relative to geoid requires a geoid model.",
            }
        except (KeyError, OSError, UnicodeError, ValueError, ET.ParseError) as error:
            errors.append(f"Could not validate LOLA product metadata or raster: {error}")

    result["validation_status"] = (
        "FAILED" if errors else "PASSED_WITH_WARNINGS" if warnings else "PASSED"
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["validation_status"] != "FAILED" else 1)
