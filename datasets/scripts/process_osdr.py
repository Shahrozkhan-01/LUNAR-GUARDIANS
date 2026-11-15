"""Process public OSD-53 sample metadata and aggregate fold-change data."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datasets" / "raw" / "astronaut_health" / "osdr"
OUT = ROOT / "datasets" / "processed" / "astronaut_health" / "osdr"
PROCESSED_ZIP = RAW / "GLDS-53_microarray_E-GEOD-47126.processed.zip"
ADDITIONAL_ZIP = RAW / "GLDS-53_microarray_E-GEOD-47126.additional.zip"
ISA_ZIP = RAW / "OSD-53_metadata_OSD-53-ISA.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    samples = []
    with ZipFile(ISA_ZIP) as archive:
        lines = archive.read("s_OSD-53.txt").decode("utf-8-sig").splitlines()
        reader = csv.DictReader(lines, delimiter="\t")
        for row in reader:
            samples.append(
                {
                    "sample_id": row.get("Sample Name", ""),
                    "organism": row.get("Characteristics[Organism]", ""),
                    "material_type": row.get("Characteristics[Material Type]", ""),
                    "spaceflight": row.get("Factor Value[Spaceflight]", ""),
                    "time": row.get("Factor Value[Time]", ""),
                }
            )
    sample_path = OUT / "osd53_sample_metadata.csv"
    with sample_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=samples[0].keys())
        writer.writeheader()
        writer.writerows(samples)

    with ZipFile(ADDITIONAL_ZIP) as archive:
        text = archive.read("GSE47126_Fold_change_data.txt").decode("utf-8-sig")
    rows = list(csv.reader(text.splitlines(), delimiter="\t"))
    header = rows[0]
    gene_rows = []
    for row in rows[3:]:
        if not row or not row[0]:
            continue
        values = row + [""] * (len(header) - len(row))
        gene_rows.append(
            {
                "gene_id": values[0],
                "probe_id": values[1],
                "preflight_average": values[14],
                "postflight_average": values[15],
                "ratio": values[16],
                "log2_ratio": values[17],
                "f_test": values[18],
                "p_value": values[19],
                "adjusted_p_value": values[20],
            }
        )
    gene_path = OUT / "osd53_gene_expression_summary.csv"
    with gene_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=gene_rows[0].keys())
        writer.writeheader()
        writer.writerows(gene_rows)

    metadata = {
        "dataset_id": "OSD-53",
        "genelab_id": "GLDS-53",
        "title": "Spaceflight Modulates Gene Expression in Astronauts",
        "organism": "Homo sapiens",
        "source_urls": [
            "https://osdr.nasa.gov/bio/repo/data/studies/OSD-53",
            "https://osdr.nasa.gov/geode-py/ws/repo/studies/OSD-53",
        ],
        "record_count": len(samples),
        "gene_summary_count": len(gene_rows),
        "variables": {
            "sample_metadata": "Public OSDR processed sample annotations",
            "preflight_average": "Processed array signal average; source unit not supplied",
            "postflight_average": "Processed array signal average; source unit not supplied",
            "ratio": "Post-flight/pre-flight ratio as supplied by source",
            "log2_ratio": "Log2 ratio as supplied by source",
            "p_value": "Source statistical field; not a clinical measure",
        },
        "missing_value_policy": "Blank source fields remain blank; no imputation.",
        "raw_data_availability": "Original raw microarray data reported unavailable by OSDR.",
        "privacy_policy": "No individual identities are displayed; study-subject labels are removed from processed output.",
        "transformations": [
            "Extracted public sample annotations from OSDR processed archive.",
            "Extracted source fold-change summary and retained source numeric fields.",
            "Removed study-subject identifiers from the processed sample table.",
        ],
        "source_sha256": {
            "processed_zip": sha256(PROCESSED_ZIP),
            "additional_zip": sha256(ADDITIONAL_ZIP),
            "isa_zip": sha256(ISA_ZIP),
        },
        "processed_output_readback_verified": True,
    }
    (OUT / "osd53_processing_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    summary = {
        "sample_count": len(samples),
        "gene_summary_count": len(gene_rows),
        "preflight_sample_count": sum("Baseline" in row["spaceflight"] for row in samples),
        "postflight_sample_count": sum("Space Flight" in row["spaceflight"] for row in samples),
        "organism": "Homo sapiens",
        "historical_human_research": True,
        "clinical_interpretation": False,
    }
    (OUT / "osd53_summary_statistics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
