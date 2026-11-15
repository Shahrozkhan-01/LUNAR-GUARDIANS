# Diviner GCP processing

## Source product and scope

This processing output is derived from the existing NASA PDS3 Diviner Global
Cumulative Average Product `global_cumul_avg_cyl_80s70s_002`, dataset
`LRO-L-DLRE-5-GCP-V1.0`. The original PDS table and labels remain unchanged in
[`datasets/raw/lunar_environment/diviner/`](../datasets/raw/lunar_environment/diviner/).
The product covers **70°S to 80°S latitude and all longitudes**, not the entire
Moon. Its compiled nadir observations span 2009-07-05T16:50:26.195 to
2015-04-01T00:00:00.000.

The PDS label defines a 113-byte header and 1,382,400 fixed-width ASCII data
records. The associated [`dlre_gcp.fmt`](../datasets/raw/lunar_environment/diviner/dlre_gcp.fmt)
defines each column's byte offsets, widths, source data type, units and
sentinels. The PDS XML label identifies latitude as planetocentric and
longitude direction as positive east. The grid is binned at 0.5° latitude and
longitude and 0.25 hours of local time.

## Columns

Every source field is PDS `ASCII_REAL`; in the processed CSV its logical type
is nullable floating point (`float64`). Names are descriptive normalizations;
source-to-output mappings and byte offsets are retained in the processing
metadata JSON.

| Source | Processed column | Meaning from PDS format | Unit |
|---|---|---|---|
| `clon` | `center_longitude_deg` | Tile center longitude | degree, positive east |
| `clat` | `center_latitude_deg` | Tile center planetocentric latitude | degree |
| `ltim` | `local_time_hour` | Local time | hour |
| `t3` | `brightness_temperature_channel_3_k` | Channel 3 average calibrated brightness temperature | K |
| `t4` | `brightness_temperature_channel_4_k` | Channel 4 average calibrated brightness temperature | K |
| `t5` | `brightness_temperature_channel_5_k` | Channel 5 average calibrated brightness temperature | K |
| `t6` | `brightness_temperature_channel_6_k` | Channel 6 average calibrated brightness temperature | K |
| `t7` | `brightness_temperature_channel_7_k` | Channel 7 average calibrated brightness temperature | K |
| `t8` | `brightness_temperature_channel_8_k` | Channel 8 average calibrated brightness temperature | K |
| `t9` | `brightness_temperature_channel_9_k` | Channel 9 average calibrated brightness temperature | K |
| `tbol` | `brightness_temperature_bolometric_k` | Bolometric average calibrated brightness temperature | K |

These are **brightness temperatures**, not ordinary air temperature, an
in-situ surface thermometer, habitat temperature, or astronaut temperature.
The source label explains that negative brightness-temperature values can
result from negative radiance when a signal is below channel sensitivity.
Such values are preserved as valid source values; no arbitrary temperature
limits are applied.

## Processing and missing values

Run from the repository root:

```powershell
.\backend\venv\Scripts\python.exe .\datasets\scripts\process_diviner_dataset.py
```

The script reads one PDS record at a time and uses the PDS format definition's
byte offsets rather than guessing a delimiter or assuming a general CSV
layout. It checks the source header, record width, row count, ASCII content,
and file size against the PDS label. The output retains every row and every
valid numeric field's original text representation. Only documented sentinel
values are mapped to empty CSV fields:

- `-9999`: PDS unknown/no-observation value.
- `-9998`: PDS invalid value.

Both sentinel counts are recorded separately by field. No `-9998` values were
present in this source. Negative brightness-temperature values are not
reclassified as missing or invalid. The script reopens the compressed output
and compares it row-by-row and field-by-field with the raw table, allowing only
the documented sentinel-to-empty-field conversion. It also checks the raw
table SHA-256 before and after processing.

The output is deterministic gzip-compressed CSV: the gzip timestamp is fixed,
and the CSV is streamed so the full source table is not loaded into memory.
Exact medians are calculated from per-channel in-memory numeric arrays, one
value per valid measurement.

## Outputs and validation

Files are stored under
[`datasets/processed/lunar_environment/diviner/`](../datasets/processed/lunar_environment/diviner/):

- `global_cumul_avg_cyl_80s70s_002.csv.gz` — 39,285,835 bytes.
- `diviner_processing_metadata.json` — schema, PDS units and definitions,
  source hash, coverage, processing details, and output integrity checks.
- `diviner_summary_statistics.json` — per-column valid/missing counts,
  minimum, maximum, mean, median for temperature fields, negative brightness
  counts, and coordinate/local-time coverage and frequency distribution.

**Result:** 1,382,400 source rows and 1,382,400 output rows. Row-by-row
readback confirmed that every non-sentinel value is preserved. There are
349,523 rows with at least one documented missing or invalid sentinel, all
due to `-9999` unknown/no-observation values. No `-9998` invalid sentinels or
documented out-of-range coordinates were found. There are 1,382,400 rows
without a documented invalid sentinel or coordinate outside the label's
coverage. All 20 latitude centers, 720 longitude centers, and 96 local-time
bins are present. Each local-time bin has 14,400 records.

### Temperature summary

Statistics below use valid, non-sentinel values only. Negative values remain
included. The PDS label provides no hard physical minimum/maximum for these
brightness-temperature columns.

| Field | Valid | `-9999` missing | Minimum (K) | Maximum (K) | Mean (K) | Median (K) | Negative values |
|---|---:|---:|---:|---:|---:|---:|---:|
| `t3` | 1,042,843 | 339,557 | -185.3031 | 354.1131 | 84.6595 | 143.9890 | 398,247 |
| `t4` | 1,041,247 | 341,153 | -187.4221 | 354.4487 | 75.7453 | 144.8605 | 422,772 |
| `t5` | 1,040,648 | 341,752 | -181.3647 | 341.3992 | 121.4759 | 149.5113 | 258,233 |
| `t6` | 1,038,568 | 343,832 | -96.6507 | 338.1008 | 146.2901 | 98.5340 | 15,775 |
| `t7` | 1,038,814 | 343,586 | -66.0242 | 344.8546 | 139.7629 | 94.0098 | 800 |
| `t8` | 1,042,055 | 340,345 | -46.5180 | 346.9067 | 136.2756 | 91.3134 | 4 |
| `t9` | 1,043,558 | 338,842 | 36.4347 | 439.0000 | 134.6001 | 92.7632 | 0 |
| `tbol` | 1,043,558 | 338,842 | 36.4099 | 348.8926 | 150.6062 | 94.9124 | 0 |

Coordinates span longitude centers -179.75° to 179.75° and planetocentric
latitude centers -79.75° to -70.25°. Local-time centers span 0.12 to 23.88
hours (96 quarter-hour bins).

## Limitations and possible educational use

This is a historical, multi-year, spatially and locally time-binned product,
not a live temperature feed or forecast. It covers a south-polar latitude
band rather than a specific outpost site and does not directly measure the
temperature of a habitat, astronaut, or every point on the surface. Its
brightness-temperature measurements should not be presented as ordinary air
temperature or as exact outpost conditions.

The processed data can support future analysis or educational comparisons of
how Diviner brightness temperature varies by location and local time. It is
not connected to the game engine or frontend and has not been used to create
gameplay resource values or consequences.

## References

- [NASA PDS Diviner GCP dataset label](../datasets/raw/lunar_environment/diviner/global_cumul_avg_cyl_80s70s_002.lbl)
- [PDS fixed-width format definition](../datasets/raw/lunar_environment/diviner/dlre_gcp.fmt)
- [Original Diviner dataset documentation](diviner_dataset.md)
- [NASA PDS Diviner archive](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm)
