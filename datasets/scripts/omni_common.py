"""Shared parsing definitions for the NASA OMNI2 hourly product."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


FIELDS = [
    ("year", int), ("day_of_year", int), ("hour", int),
    ("bartels_rotation", int), ("imf_spacecraft_id", int),
    ("plasma_spacecraft_id", int), ("imf_points", int), ("plasma_points", int),
    ("imf_magnitude_nt", float), ("field_vector_magnitude_nt", float),
    ("field_vector_latitude_deg", float), ("field_vector_longitude_deg", float),
    ("bx_gse_nt", float), ("by_gse_nt", float), ("bz_gse_nt", float),
    ("by_gsm_nt", float), ("bz_gsm_nt", float), ("sigma_b_magnitude_nt", float),
    ("sigma_b_vector_nt", float), ("sigma_bx_nt", float), ("sigma_by_nt", float),
    ("sigma_bz_nt", float), ("proton_temperature_k", float),
    ("proton_density_cm3", float), ("solar_wind_speed_km_s", float),
    ("flow_longitude_deg", float), ("flow_latitude_deg", float),
    ("alpha_proton_ratio", float), ("flow_pressure_npa", float),
    ("sigma_temperature_k", float), ("sigma_density_cm3", float),
    ("sigma_speed_km_s", float), ("sigma_flow_longitude_deg", float),
    ("sigma_flow_latitude_deg", float), ("sigma_alpha_proton_ratio", float),
    ("electric_field_mv_m", float), ("plasma_beta", float),
    ("alfven_mach_number", float), ("kp_index", int), ("sunspot_number", int),
    ("dst_index_nt", int), ("ae_index_nt", int), ("proton_flux_gt_1_mev", float),
    ("proton_flux_gt_2_mev", float), ("proton_flux_gt_4_mev", float),
    ("proton_flux_gt_10_mev", float), ("proton_flux_gt_30_mev", float),
    ("proton_flux_gt_60_mev", float), ("proton_flux_flag", int),
    ("ap_index_nt", int), ("f107_index_sfu", float), ("pcn_index", float),
    ("al_index_nt", int), ("au_index_nt", int), ("magnetosonic_mach_number", float),
]

FILL_VALUES = {
    "bartels_rotation": 9999, "imf_spacecraft_id": 99,
    "plasma_spacecraft_id": 99, "imf_points": 999, "plasma_points": 999,
    "imf_magnitude_nt": 999.9, "field_vector_magnitude_nt": 999.9,
    "field_vector_latitude_deg": 999.9, "field_vector_longitude_deg": 999.9,
    "bx_gse_nt": 999.9, "by_gse_nt": 999.9, "bz_gse_nt": 999.9,
    "by_gsm_nt": 999.9, "bz_gsm_nt": 999.9, "sigma_b_magnitude_nt": 999.9,
    "sigma_b_vector_nt": 999.9, "sigma_bx_nt": 999.9, "sigma_by_nt": 999.9,
    "sigma_bz_nt": 999.9, "proton_temperature_k": 9999999.0,
    "proton_density_cm3": 999.9, "solar_wind_speed_km_s": 9999,
    "flow_longitude_deg": 999.9, "flow_latitude_deg": 999.9,
    "alpha_proton_ratio": 9.999, "flow_pressure_npa": 99.99,
    "sigma_temperature_k": 9999999.0, "sigma_density_cm3": 999.9,
    "sigma_speed_km_s": 9999, "sigma_flow_longitude_deg": 999.9,
    "sigma_flow_latitude_deg": 999.9, "sigma_alpha_proton_ratio": 9.999,
    "electric_field_mv_m": 999.99, "plasma_beta": 999.99,
    "alfven_mach_number": 999.9, "kp_index": 99, "sunspot_number": 999,
    "dst_index_nt": 99999, "ae_index_nt": 9999,
    "proton_flux_gt_1_mev": 999999.99, "proton_flux_gt_2_mev": 99999.99,
    "proton_flux_gt_4_mev": 99999.99, "proton_flux_gt_10_mev": 99999.99,
    "proton_flux_gt_30_mev": 99999.99, "proton_flux_gt_60_mev": 99999.99,
    "proton_flux_flag": 0, "ap_index_nt": 999, "f107_index_sfu": 999.9,
    "pcn_index": 999.9, "al_index_nt": 99999, "au_index_nt": 99999,
    "magnetosonic_mach_number": 99.9,
}


def parse_line(line: str) -> dict[str, Any]:
    tokens = line.split()
    if len(tokens) != len(FIELDS):
        raise ValueError(f"expected {len(FIELDS)} fields, found {len(tokens)}")
    record: dict[str, Any] = {}
    for (name, converter), token in zip(FIELDS, tokens):
        record[name] = converter(token)
    record["timestamp_utc"] = (
        datetime(record["year"], 1, 1, tzinfo=timezone.utc)
        + timedelta(days=record["day_of_year"] - 1, hours=record["hour"])
    ).isoformat().replace("+00:00", "Z")
    return record


def iter_records(path: Path):
    with path.open("r", encoding="ascii") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                yield line_number, parse_line(line)
            except ValueError as exc:
                raise ValueError(f"line {line_number}: {exc}") from exc


def is_missing(name: str, value: Any) -> bool:
    fill = FILL_VALUES.get(name)
    return fill is not None and value == fill
