# Diviner south-polar temperature dataset

## Dataset selected

This project now includes one manageable regional subset from the NASA Planetary
Data System (PDS) Diviner archive:

- **Product:** LRO Diviner Global Cumulative Average Product,
  `global_cumul_avg_cyl_80s70s_002`
- **PDS data set ID:** `LRO-L-DLRE-5-GCP-V1.0`
- **Coverage:** 70°S to 80°S latitude, all longitudes (-180° to 180°), on the
  documented planetocentric coordinate system
- **Observation period:** 2009-07-05T16:50:26.195 through 2015-04-01T00:00:00.000
- **File:** `global_cumul_avg_cyl_80s70s_002.tab` (156,211,313 bytes; about
  148.95 MiB)
- **Format:** PDS3 fixed-length ASCII table, 113-byte records, 1,382,400 data
  rows and 11 columns. The file begins with a column-name record; the original
  product bytes have not been transformed.
- **Product identifier:** `GLOBAL_CUMUL_AVG_CYL_80S70S_002.TAB`

The archive's product label says the observations were binned at 0.5° latitude
and longitude and 0.25 hours of local time. That gives 720 longitude centers,
20 latitude centers and 96 local-time centers in this subset.

## What Diviner measures

The Diviner Lunar Radiometer Experiment on the Lunar Reconnaissance Orbiter
measures infrared and reflected solar radiation. This product contains
calibrated **brightness temperatures**, including spectral-channel brightness
temperatures and bolometric brightness temperature. Brightness temperature is
not interchangeable with a direct measurement of the temperature of an
astronaut, habitat interior, or every point on the lunar surface.

The columns and units are defined by the accompanying PDS format file:

| Variable | Meaning | Unit |
|---|---|---|
| `clon` | Tile center longitude | degrees |
| `clat` | Tile center latitude | degrees |
| `ltim` | Local time | hours |
| `t3`–`t9` | Average calibrated brightness temperatures for Diviner channels 3–9 | K |
| `tbol` | Bolometric average calibrated brightness temperature | K |

`-9999` is the documented unknown/no-observation value; `-9998` is the
documented invalid value. The PDS label explicitly notes that some negative
brightness-temperature values can result from negative radiance when a signal
is below a channel's sensitivity. They are retained as source values and are
not incorrectly treated as missing or deleted.

The PDS GCP label does not publish hard minimum/maximum physical bounds for
these brightness-temperature columns. The validator therefore checks their
numeric form, finiteness and documented missing/invalid sentinels without
inventing a temperature threshold; it separately enforces documented
coordinate and local-time bounds.

## Source and downloaded files

The official [Diviner data archive](https://www.diviner.ucla.edu/data) points to
the [NASA PDS Geosciences Node LRO Diviner archive](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm).
The selected product is listed in its official
[GCP collection](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/).
The direct data download is
[global_cumul_avg_cyl_80s70s_002.tab](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/global_cumul_avg_cyl_80s70s_002.tab).
Its source label, PDS4 XML label, shared column format, and Diviner Reduced Data
Record Software Interface Specification were also downloaded from that same
PDS archive into `datasets/raw/lunar_environment/diviner/`.

The original data file's SHA-256 is:

`C6C9B3A84E1E9972237B07FD8DD1C0F44899AB8FFE9A403A7528EF7CD38B1CDA`

The PDS labels and SIS are authoritative for product identifiers, dates,
coverage, column definitions, units and sentinel semantics. The source and
validation status are also recorded in
[`datasets/metadata/dataset_catalog.csv`](../datasets/metadata/dataset_catalog.csv).

## Validation

Run the validator from the repository root:

```powershell
.\backend\venv\Scripts\python.exe datasets\scripts\validate_diviner_dataset.py
```

The script uses Python's standard library to read the PDS format definition and
scan every fixed-size record. It checks file presence and size against the PDS
label, the table header and column layout, data-row count, ASCII content,
numeric/finiteness and documented sentinel values, coordinate bounds and
coordinate-grid counts. It does not rewrite, remove or convert raw measurements.
The JSON report is written to
`datasets/validation_reports/diviner_gcp_80s70s_validation.json`.

**Validation result: PASSED.** All 1,382,400 rows and 11 columns were read.
The file size matches the PDS label exactly; the longitude, latitude and local
time grids contain 720, 20 and 96 centers respectively. Coordinates are within
the label's documented coverage, and there are no invalid (`-9998`),
unparsable, non-finite, off-grid or out-of-range values. The `-9999` missing
counts for temperature fields are reported per variable in the JSON report.
Observed negative brightness-temperature values are retained and noted in the
report according to the PDS documentation. No undocumented physical
temperature limits were applied.

## Scientific limitations and use

This is a historical, compiled product from nadir observations acquired over
multiple years, not a live temperature feed or a forecast. It covers a broad
south-polar latitude band, not the specific Shackleton Rim outpost location.
Spatial and local-time binning, instrument sensitivity, missing observations,
calibration and product algorithms limit how directly values can be applied to
a particular site or activity. The data are not an in-situ thermometer reading
for an outpost.

The dataset is cataloged and validated only. **It is not connected to gameplay**
and currently changes no mission resources, events or environmental state.
Potential educational use is to teach that lunar surface brightness
temperatures vary by location and local time; any later game application will
need explicit scientific modeling and retain the source limitations.

## References

- [Diviner official data page](https://www.diviner.ucla.edu/data)
- [NASA PDS Geosciences Node LRO Diviner archive](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm)
- [PDS GCP collection](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/)
- [Diviner RDR Software Interface Specification (PDF)](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/document/Diviner_RDR_SIS.pdf)
- Williams et al. (2017), “The global surface temperatures of the Moon as
  measured by the Diviner Lunar Radiometer Experiment,” *Icarus* 283, 300–325,
  DOI: [10.1026/j.icarus.2016.08.012](https://doi.org/10.1026/j.icarus.2016.08.012).
