# NASA LRO LEND DLD/DLX dataset

## Selection and provenance

This integration preserves one bounded day, 2020-01-01 UTC, from the official
NASA PDS Geosciences LRO LEND archive:

- [LEND archive](https://pds-geosciences.wustl.edu/missions/lro/lend.htm)
- [RDR SIS](https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/document/lend_rdr_sis.htm)
- Products: `LEND_RDR_DLD_20200101_DAT` and `LEND_RDR_DLX_20200101_DAT`
- PDS4 identifiers:
  `urn:nasa:pds:lro_lend:data_science_derived:lend_rdr_dld_20200101` and
  `urn:nasa:pds:lro_lend:data_science_derived:lend_rdr_dlx_20200101`

The original binary files, PDS3 labels, PDS4 XML labels, and RDR SIS are
preserved under `datasets/raw/lunar_environment/lend/`. The DLD table has
85,308 239-byte records and the DLX table has 85,308 71-byte records.

## Processing and validation

`datasets/scripts/validate_lend_dataset.py` checks fixed-record sizes,
timestamps, DLD/DLX alignment, duplicate timestamps, latitude/longitude
ranges, and finite numeric values. Its report is
`datasets/validation_reports/lend_validation.json` and is
`PASS_WITH_WARNINGS`.

`datasets/scripts/process_lend_dataset.py` decodes the official big-endian
binary fields and joins DLD and DLX rows by `LRO_TIME` and UTC. It produces
`datasets/processed/lunar_environment/lend/lend_20200101_processed.csv`,
metadata, and summary statistics. No values are imputed, converted to flux or
dose, or silently removed. Negative corrected-count and sigma values remain
visible because the source defines them as unusable markers.

The source DLD label has two documented anomalies: overlapping SHEN field
definitions and a `km/s` unit attached to `STN2_COUNTS` despite its detector
count description. The parser does not decode the overlapping SHEN fields and
preserves the source warning rather than guessing a scientific correction.

## Application use and limitations

LEND is an orbital lunar neutron observation. The explorer shows the track
latitude/longitude, detector counts, corrected CSETN sum, and sigma values
with their source units. These are historical observations, not current
telemetry, surface measurements, astronaut radiation dose, or habitat
conditions. The application does not infer water ice at a specific location
from this sample and does not connect the measurements to simulated game
consequences.
