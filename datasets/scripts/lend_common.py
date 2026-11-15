"""Shared parser for the bounded PDS LEND DLD and DLX binary products."""

from __future__ import annotations

import csv
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List


DLD_RECORD_BYTES = 239
DLX_RECORD_BYTES = 71
RECORD_COUNT = 85308

DLD_FIELDS = {
    "lro_time": (0, ">Q"),
    "utc": (8, "ascii23"),
    "local_hour": (31, ">B"),
    "local_minute": (32, ">B"),
    "lunarcentric_latitude_deg": (33, ">f"),
    "lunarcentric_east_longitude_deg": (37, ">f"),
    "collection_duration_s": (41, ">I"),
    "stn1_background_counts": (45, ">f"),
    "stn1_counts": (49, ">f"),
    "setn_background_counts": (53, ">f"),
    "setn_counts": (57, ">f"),
    "stn2_background_counts": (61, ">f"),
    "stn2_counts": (65, ">f"),
    "stn3_background_counts": (69, ">f"),
    "stn3_counts": (73, ">f"),
    "csetn1_background_counts": (77, ">f"),
    "csetn1_counts": (81, ">f"),
    "csetn2_background_counts": (85, ">f"),
    "csetn2_counts": (89, ">f"),
    "csetn3_background_counts": (93, ">f"),
    "csetn3_counts": (97, ">f"),
    "csetn4_background_counts": (101, ">f"),
    "csetn4_counts": (105, ">f"),
    "sun_activity": (237, ">B"),
    "nadir_pointing": (238, ">B"),
}

DLX_FIELDS = {
    "lro_time": (0, ">Q"),
    "utc": (8, "ascii23"),
    "csetn_sum_counts": (31, ">f"),
    "csetn_sum_sigma_counts": (35, ">f"),
    "csetn1_sigma_counts": (39, ">f"),
    "csetn2_sigma_counts": (43, ">f"),
    "csetn3_sigma_counts": (47, ">f"),
    "csetn4_sigma_counts": (51, ">f"),
    "setn_sigma_counts": (55, ">f"),
    "stn1_sigma_counts": (59, ">f"),
    "stn2_sigma_counts": (63, ">f"),
    "stn3_sigma_counts": (67, ">f"),
}


def _decode(record: bytes, offset: int, kind: str):
    if kind == "ascii23":
        return record[offset : offset + 23].decode("ascii").strip()
    return struct.unpack(kind, record[offset : offset + struct.calcsize(kind)])[0]


def parse_binary(path: Path, record_bytes: int, fields: Dict[str, tuple[int, str]]) -> Iterator[dict]:
    with path.open("rb") as stream:
        index = 0
        while record := stream.read(record_bytes):
            if len(record) != record_bytes:
                raise ValueError(f"Truncated record {index}: {len(record)} bytes")
            row = {name: _decode(record, offset, kind) for name, (offset, kind) in fields.items()}
            row["record_index"] = index
            yield row
            index += 1


def normalize_number(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def load_records(raw_directory: Path) -> List[dict]:
    dld = list(parse_binary(raw_directory / "lend_rdr_dld_20200101.dat", DLD_RECORD_BYTES, DLD_FIELDS))
    dlx = list(parse_binary(raw_directory / "lend_rdr_dlx_20200101.dat", DLX_RECORD_BYTES, DLX_FIELDS))
    if len(dld) != len(dlx):
        raise ValueError("DLD and DLX record counts do not match")
    records = []
    for left, right in zip(dld, dlx):
        if left["utc"] != right["utc"] or left["lro_time"] != right["lro_time"]:
            raise ValueError(f"DLD/DLX timestamp mismatch at record {left['record_index']}")
        row = {key: normalize_number(value) for key, value in left.items() if key != "record_index"}
        row.update({key: normalize_number(value) for key, value in right.items() if key not in ("record_index", "lro_time", "utc")})
        row["record_index"] = left["record_index"]
        row["timestamp_utc"] = row.pop("utc") + "Z"
        records.append(row)
    return records


def write_csv(records: Iterable[dict], path: Path) -> None:
    records = list(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
