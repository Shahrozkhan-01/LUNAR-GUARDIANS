# LOLA LDEM_16 global elevation dataset

## Dataset acquired

- **Product:** Lunar Reconnaissance Orbiter (LRO) LOLA gridded shape/elevation
  image, `LDEM_16`
- **PDS data set ID:** `LRO-L-LOLA-4-GDR-V1.0`
- **PDS4 logical identifier:** `urn:nasa:pds:lro_lola_rdr:data_gridded:ldem_16`
- **Source:** [NASA PDS Geosciences Node LOLA RDR archive](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/)
- **Direct raster:** [ldem_16.img](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_16.img)
- **Retrieved:** 2026-11-14
- **Coverage:** global, 0°–360° east longitude and 90°N–90°S planetocentric
  latitude
- **Source observation interval:** 2009-07-13T17:33:17 through
  2016-11-29T05:48:19 UTC
- **Grid:** 5,760 samples by 2,880 lines; 16 pixels per degree; PDS label scale
  1,895.21 m/pixel

The product was selected as a compact, global, coarse-resolution terrain layer
that includes the lunar south polar region. The label describes it as a
shape/radius map built from geolocated LOLA altimetry and interpolated gridded
products. Its use is broad-scale terrain context, not a local landing-site
hazard survey.

## Files and preservation

All five files were saved unchanged from the official PDS bundle in
`datasets/raw/lunar_environment/lola/`:

| File | Purpose | Bytes |
|---|---|---:|
| `ldem_16.img` | Original binary elevation raster | 33,177,600 |
| `ldem_16.lbl` | PDS3 product label | 5,121 |
| `ldem_16.xml` | PDS4 product label | 11,941 |
| `dsmap.cat` | Referenced map-projection definition | 7,378 |
| `rdrsis.pdf` | LOLA RDR Software Interface Specification | 802,914 |

Total downloaded: **34,004,954 bytes** (about 32.43 MiB). The raster alone is
about 31.64 MiB. The raster's local SHA-256 is
`A511E40D7A3EA3275945B4DA2A1DF377133264FAB0BE94B7434B1CF8907254CB`.
This checksum identifies the local copy; an independent per-file source
checksum was not listed with this product.

## Variables, units, and encoding

The image contains one variable, `HEIGHT`. Samples are stored as signed
16-bit little-endian integers. The PDS label specifies `UNIT = METER` and
`SCALING_FACTOR = 0.5`; therefore the height value in meters relative to the
product's reference radius is the stored sample multiplied by 0.5. The label's
`OFFSET = 1,737,400 m` is the spherical reference radius used to calculate
planetary radius (`sample * 0.5 + offset`). The raster is not itself a
geoid-referenced topographic-height product; deriving topography relative to
the geoid requires a geoid model.

The PDS3 label reports `MINIMUM = -18150` and `MAXIMUM = 21580`. The full
decoded raster's observed stored-sample range is **-17963 to 21371**, or
**-8981.5 to 10685.5 m** after the label's 0.5 scaling. All samples lie within
the label's stated bounds, but the extrema do not exactly equal the label
values. The validator records this discrepancy as a warning; confirm the
label/data extrema difference with PDS before relying on extreme values.

The product label does not define a missing-value sentinel. No presumed fill
value was applied, and no data values were removed or rewritten.

## Coordinate reference and observation period

The PDS labels specify a **simple cylindrical** map projection, with pixel
registration, centered at 0° latitude and 180° longitude. The coordinate
system is body-fixed rotating, `MEAN EARTH/POLAR AXIS OF DE421`; latitude is
planetocentric, and longitude increases eastward from 0° to 360°. The
projection equations and offsets are in the accompanying `dsmap.cat`.

The temporal interval describes the LOLA observations contributing to this
gridded product. It is not a time series: each raster cell is not associated
with a per-pixel observation time in this image.

## Validation

Run the standard-library validator from the repository root:

```powershell
.\backend\venv\Scripts\python.exe datasets\scripts\validate_lola_ldem.py
```

The script checks file presence, byte size against both the PDS directory
listing and label dimensions, decodability of every signed 16-bit pixel,
observed sample bounds against label extrema, required PDS identifiers and
dates, coordinate ranges, map projection metadata, and consistency between
grid dimensions and geographic coverage. It computes a SHA-256 for each local
file. The report is written to
`datasets/validation_reports/lola_ldem_16_validation.json`.

**Result: PASSED_WITH_WARNINGS.** The 33,177,600-byte raster has exactly
16,588,800 samples (5,760 × 2,880), its dimensions and file size match the
PDS labels, all samples decode, metadata identifiers and observation dates
agree across labels, and observed samples are within the label's declared
range. The mismatch between observed and label extrema is preserved as an
explicit warning. No documented missing sentinel is specified.

## Relevance and limitations for an outpost

LOLA is the Lunar Orbiter Laser Altimeter aboard LRO. It measures surface
elevation/range with laser altimetry; the archive's gridded DEM products
provide broad topographic context. A coarse global grid can help introduce
regional elevation differences and discuss why terrain information matters
when comparing candidate areas.

This product's approximately 1.9 km/pixel nominal sampling is far too coarse
to assess boulders, local slopes, crater rims, landing hazards, or the
construction footprint of a habitat. Simple cylindrical projection has
strong spatial distortion at high latitudes: degrees of longitude do not
represent uniform ground distance near the poles. The grid was interpolated
from a finite set of altimeter observations; source label notes potential
artifacts at 45-degree latitude-band boundaries. The height values are
relative to the stated reference sphere, not automatically local elevation
above a geoid or a specific landing-site datum.

The data is cataloged and validated only. **It is not connected to gameplay**
and does not change mission events, resources, maps, or environmental state.
No Diviner data was processed as part of this acquisition.

## References

- [NASA PDS LOLA archive description](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)
- [PDS LOLA RDR bundle README](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/readme.txt)
- [LDEM_16 PDS3 label](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_16.lbl)
- [LDEM_16 PDS4 XML label](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_16.xml)
- [LOLA RDR Software Interface Specification](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/document/rdrsis.pdf)
- [Lunar Orbital Data Explorer](https://ode.rsl.wustl.edu/moon/)
